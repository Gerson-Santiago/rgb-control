import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Gdk
import logging

logger = logging.getLogger(__name__)

try:
    from rgb_control.backend import Backend
except ImportError:
    from backend import Backend

def get_asset_path(filename):
    """Retorna o caminho do asset, buscando localmente ou na estrutura do .deb"""
    # __file__ is src/rgb_control/window.py -> dirname is src/rgb_control -> dirname(dirname) is src/
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(src_dir)
    
    # Busca na pasta assets/ na raiz do projeto (dev)
    for base in [root_dir, src_dir]:
        for sub in ["assets", "rgb_control/assets"]:
            path = os.path.join(base, sub, filename)
            if os.path.exists(path):
                return path
            
    # Fallback para instalação global no Debian
    global_path = os.path.join('/usr/share/rgb-control/assets', filename)
    if os.path.exists(global_path):
        return global_path
        
    return os.path.join(root_dir, filename)

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        self._updating_ui = False # Previne loops infinitos de sinais
        super().__init__(application=application)
        self.set_title("RGB Control")
        # Tamanho mais generoso e ergonômico
        self.set_default_size(550, 750)
        
        logger.info("Carregando interface Libadwaita Premium...")
        self.backend = Backend()
        
        # Carregar CSS Global
        self.load_custom_css()
        
        # 1. ToolbarView (Root)
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)
        
        # 2. HeaderBar
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(Adw.WindowTitle(title="OpenRBG", subtitle="Controle de Iluminação"))
        
        # Menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        theme_section = Gio.Menu()
        theme_section.append("Tema Claro", "app.theme_light")
        theme_section.append("Tema Escuro", "app.theme_dark")
        theme_section.append("Padrão do Sistema", "app.theme_system")
        menu.append_section(None, theme_section)
        menu_button.set_menu_model(menu)
        self.header.pack_end(menu_button)
        self.toolbar_view.add_top_bar(self.header)
        
        # 3. Conteúdo Principal com Clamp (Centralização Responsiva)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        clamp = Adw.Clamp()
        clamp.set_maximum_size(500) # Mantém os controles elegantes no centro
        clamp.set_tightening_threshold(400)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        main_box.set_margin_top(32)
        main_box.set_margin_bottom(32)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        
        # --- Hero Section (Logo e Status Principal) ---
        logo_path = get_asset_path("logo.svg")
        if os.path.exists(logo_path):
            hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            hero_box.set_halign(Gtk.Align.CENTER)
            
            self.logo = Gtk.Picture.new_for_filename(logo_path)
            self.logo.set_size_request(160, 160)
            self.logo.add_css_class("logo-main")
            
            hero_box.append(self.logo)
            
            title_label = Gtk.Label()
            title_label.set_markup("<span size='x-large' weight='bold'>Personalize seu Setup</span>")
            hero_box.append(title_label)
            
            main_box.append(hero_box)

        # --- Grupos de Preferências ---
        
        # Grupo 1: Status e Sistema
        system_group = Adw.PreferencesGroup()
        system_group.set_title("Configurações do Serviço")
        
        self.switch_svc = Adw.SwitchRow()
        self.switch_svc.set_title("Serviço OpenRBG (Background)")
        self.switch_svc.set_subtitle("Gerencia a conexão com o hardware")
        self.switch_svc.set_active(self.backend.is_service_active())
        self.switch_svc.connect("notify::active", self.on_service_notify)
        system_group.add(self.switch_svc)
        
        self.switch_mode = Adw.SwitchRow()
        self.switch_mode.set_title("Modo de Captura LED")
        self.switch_mode.set_subtitle("Permite controle via Air Mouse")
        self.switch_mode.set_active(self.backend.is_led_mode_active())
        self.switch_mode.connect("notify::active", self.on_mode_notify)
        system_group.add(self.switch_mode)
        
        main_box.append(system_group)
        
        # Grupo 2: Paleta de Cores
        lighting_group = Adw.PreferencesGroup()
        lighting_group.set_title("Paleta de Cores")
        lighting_group.set_description("Selecione uma cor para aplicar instantaneamente")
        
        # Container para a grade de cores
        palette_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        self.colors = [
            ("Vermelho", "#FF0000"), ("Laranja", "#FF5500"), ("Amarelo", "#FFFF00"),
            ("Verde", "#00FF00"), ("Ciano", "#00F2EA"), ("Azul", "#0000FF"),
            ("Roxo", "#AA00FF"), ("Ambar", "#FFB200"), ("Branco", "#FFFFFF"),
            ("Desativar", "#000000")
        ]
        
        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_max_children_per_line(5)
        flowbox.set_min_children_per_line(5)
        flowbox.set_row_spacing(16)
        flowbox.set_column_spacing(16)
        flowbox.set_halign(Gtk.Align.CENTER)
        
        # Gerar CSS inline para as cores caso o style.css externo falhe ou precise de reforço
        css_data = ""
        for _, hex_val in self.colors:
            cls = f"color-btn-{hex_val.strip('#')}"
            css_data += f".{cls} {{ background-color: {hex_val}; }}\n"
            
        provider = Gtk.CssProvider()
        provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        for name, hex_val in self.colors:
            btn = Gtk.Button()
            btn.add_css_class("color-btn")
            btn.add_css_class(f"color-btn-{hex_val.strip('#')}")
            btn.set_tooltip_text(name)
            btn.connect("clicked", self.on_color_clicked, hex_val, name)
            flowbox.insert(btn, -1)
            
        palette_box.append(flowbox)
        
        # Seletor Personalizado (dentro de outro grupo para destaque)
        custom_group = Adw.PreferencesGroup()
        custom_group.set_title("Cor Avançada")
        
        custom_row = Adw.ActionRow()
        custom_row.set_title("Cor Personalizada")
        custom_row.set_subtitle("Escolha qualquer cor do espectro")
        
        self.color_dialog = Gtk.ColorDialog()
        picker_btn = Gtk.ColorDialogButton()
        picker_btn.set_dialog(self.color_dialog)
        picker_btn.set_valign(Gtk.Align.CENTER)
        picker_btn.connect("notify::rgba", self.on_custom_color_selected)
        
        custom_row.add_suffix(picker_btn)
        custom_group.add(custom_row)
        
        # Unificando o Flowerbox no grupo via um widget genérico se necessário
        lighting_group.add(palette_box)
        
        main_box.append(lighting_group)
        main_box.append(custom_group)
        
        clamp.set_child(main_box)
        scrolled.set_child(clamp)
        self.toolbar_view.set_content(scrolled)
        
        self.setup_actions(application)
        GLib.timeout_add(2000, self.update_status_ui)

    def load_custom_css(self):
        """Carrega o arquivo style.css se ele existir"""
        css_path = get_asset_path("style.css")
        if os.path.exists(css_path):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            logger.info(f"CSS carregado de: {css_path}")

    def setup_actions(self, app):
        theme_light = Gio.SimpleAction.new("theme_light", None)
        theme_light.connect("activate", lambda a,p: Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT))
        app.add_action(theme_light)
        
        theme_dark = Gio.SimpleAction.new("theme_dark", None)
        theme_dark.connect("activate", lambda a,p: Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK))
        app.add_action(theme_dark)
        
        theme_system = Gio.SimpleAction.new("theme_system", None)
        theme_system.connect("activate", lambda a,p: Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.DEFAULT))
        app.add_action(theme_system)

    def on_service_notify(self, row, param):
        if self._updating_ui:
            return
        state = row.get_active()
        logger.info(f"Toggle Serviço solicitado: {state}")
        success = self.backend.set_service_state(state)
        if not success:
             logger.warning("Falha ao mudar estado do serviço no systemd")
             self._updating_ui = True
             row.set_active(not state)
             self._updating_ui = False

    def on_mode_notify(self, row, param):
        if self._updating_ui:
            return
        state = row.get_active()
        logger.info(f"Toggle Modo solicitado: {state}")
        self.backend.set_led_mode(state)

    def on_color_clicked(self, widget, hex_val, name):
        logger.info(f"Cor predefinida escolhida: {name} ({hex_val})")
        self.backend.apply_color(hex_val, name)

    def on_custom_color_selected(self, picker_btn, param):
        rgba = picker_btn.get_rgba()
        r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        self.backend.apply_color(hex_val, "Custom")

    def update_status_ui(self):
        # Sincroniza estado UI -> Background sem disparar sinais recursivos
        try:
            svc_active = self.backend.is_service_active()
            mode_active = self.backend.is_led_mode_active()
            
            self._updating_ui = True
            
            if self.switch_svc.get_active() != svc_active:
                logger.info(f"Sincronizando Switch Serviço para: {svc_active}")
                self.switch_svc.set_active(svc_active)
                
            if self.switch_mode.get_active() != mode_active:
                logger.info(f"Sincronizando Switch Modo para: {mode_active}")
                self.switch_mode.set_active(mode_active)
                
            self._updating_ui = False
        except Exception as e:
            logger.error(f"Erro na sincronização da UI: {e}")
            self._updating_ui = False
            
        return True
