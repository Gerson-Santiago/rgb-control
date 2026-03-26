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
        super().__init__(application=application)
        self.set_title("RGB Control")
        self.set_default_size(450, 700)
        
        logger.info("Carregando interface Libadwaita...")
        self.backend = Backend()
        
        # 1. ToolbarView (Modern root)
        self.toolbar_view = Adw.ToolbarView()
        
        # 2. HeaderBar
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(Adw.WindowTitle(title="OpenRBG", subtitle="Controle de LEDs"))
        
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
        
        # 3. Layout Principal (Scrollable)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        main_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Logo no topo
        logo_path = get_asset_path("logo.svg")
        if os.path.exists(logo_path):
            logo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            logo_box.set_margin_top(32)
            logo_box.set_margin_bottom(24)
            
            self.logo = Gtk.Picture.new_for_filename(logo_path)
            self.logo.set_size_request(128, 128)
            self.logo.set_halign(Gtk.Align.CENTER)
            self.logo.add_css_class("logo-main")
            
            logo_box.append(self.logo)
            main_content_box.append(logo_box)

        # 4. Preferences Page
        self.page = Adw.PreferencesPage()
        # Removido Adw.PreferencesPage do ToolbarView direto, agora vai via main_content_box
        
        # Grupo: Controle do Sistema
        system_group = Adw.PreferencesGroup()
        system_group.set_title("Status e Controle")
        system_group.set_description("Gerencie o funcionamento do daemon e do receptor")
        
        # Row: Daemon
        daemon_row = Adw.SwitchRow()
        daemon_row.set_title("Serviço OpenRBG")
        daemon_row.set_subtitle("Execução em segundo plano (systemd)")
        daemon_row.set_active(self.backend.is_service_active())
        daemon_row.connect("notify::active", self.on_service_notify)
        self.switch_svc = daemon_row
        system_group.add(daemon_row)
        
        # Row: Modo LED
        mode_row = Adw.SwitchRow()
        mode_row.set_title("Modo LED Ativo")
        mode_row.set_subtitle("Capturar botões do Air Mouse")
        mode_row.set_active(self.backend.is_led_mode_active())
        mode_row.connect("notify::active", self.on_mode_notify)
        self.switch_mode = mode_row
        system_group.add(mode_row)
        
        self.page.add(system_group)
        
        # Grupo: Iluminação
        lighting_group = Adw.PreferencesGroup()
        lighting_group.set_title("Iluminação")
        lighting_group.set_description("Escolha uma cor para os LEDs")
        
        # Grid de cores
        self.colors = [
            ("Vermelho", "#FF0000"), ("Laranja", "#FF5500"), ("Amarelo", "#FFFF00"),
            ("Verde", "#00FF00"), ("Ciano", "#00F2EA"), ("Azul", "#0000FF"),
            ("Roxo", "#AA00FF"), ("Ambar", "#FFB200"), ("Branco", "#FFFFFF"),
            ("Desligar", "#000000")
        ]
        
        # Setup Global CSS for buttons
        css = ""
        for _, hex_val in self.colors:
            cls_name = f"color-btn-{hex_val.strip('#')}"
            css += f".{cls_name} {{ background-color: {hex_val}; }}\n"
            if hex_val == "#000000":
                css += f".{cls_name} {{ border: 1px solid #555; }}\n"
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_max_children_per_line(5)
        flowbox.set_row_spacing(12)
        flowbox.set_column_spacing(12)
        flowbox.set_halign(Gtk.Align.CENTER)
        flowbox.set_margin_top(12)
        flowbox.set_margin_bottom(12)
        
        for name, hex_val in self.colors:
            btn = Gtk.Button()
            btn.add_css_class("color-btn")
            btn.add_css_class(f"color-btn-{hex_val.strip('#')}")
            btn.set_tooltip_text(name)
            btn.connect("clicked", self.on_color_clicked, hex_val, name)
            flowbox.insert(btn, -1)
            
        lighting_group.add(flowbox)
        
        # Cor Personalizada
        self.color_dialog = Gtk.ColorDialog()
        picker_btn = Gtk.ColorDialogButton()
        picker_btn.set_dialog(self.color_dialog)
        picker_btn.set_halign(Gtk.Align.CENTER)
        picker_btn.set_margin_bottom(12)
        picker_btn.connect("notify::rgba", self.on_custom_color_selected)
        
        lighting_group.add(picker_btn)
        self.page.add(lighting_group)
        
        # Adiciona a página de preferências ao box
        main_content_box.append(self.page)
        
        scrolled.set_child(main_content_box)
        self.toolbar_view.set_content(scrolled)
        self.set_content(self.toolbar_view)
        
        self.setup_actions(application)
        GLib.timeout_add(1000, self.update_status_ui)

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
        state = row.get_active()
        logger.info(f"Toggle Serviço: {state}")
        success = self.backend.set_service_state(state)
        if not success:
             GLib.idle_add(lambda: row.set_active(not state))
             return True # Indicate that the state was reverted
        return False # Indicate that the state change was accepted

    def on_mode_notify(self, row, param):
        state = row.get_active()
        logger.info(f"Toggle Modo: {state}")
        self.backend.set_led_mode(state)
        return False

    def on_color_clicked(self, widget, hex_val, name):
        logger.info(f"Cor predefinida escolhida: {name} ({hex_val})")
        self.backend.apply_color(hex_val, name)

    def on_custom_color_selected(self, picker_btn, param):
        rgba = picker_btn.get_rgba()
        r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        self.backend.apply_color(hex_val, "Custom")

    def update_status_ui(self):
        # Sincroniza estado UI -> Background
        svc_active = self.backend.is_service_active()
        if self.switch_svc.get_active() != svc_active:
            self.switch_svc.set_active(svc_active)
            
        mode_active = self.backend.is_led_mode_active()
        if self.switch_mode.get_active() != mode_active:
            self.switch_mode.set_active(mode_active)
            
        return True
