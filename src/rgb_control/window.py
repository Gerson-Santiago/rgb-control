import gi # type: ignore[import-untyped]
import gi
import os
from typing import Optional, Any, Tuple, List, Union

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Gdk # type: ignore[import-untyped]
import logging
from rgb_control.backend import Backend
from rgb_control.utils import hex_to_rgba_tuple

logger = logging.getLogger(__name__)

def get_asset_path(filename: str) -> str:
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

class MainWindow(Adw.ApplicationWindow): # type: ignore[misc]
    def __init__(self, application: Gtk.Application) -> None:
        self._updating_ui = False # Previne loops infinitos de sinais
        self._last_ctrl_connected: Optional[bool] = None # Cache do estado do controle remoto
        super().__init__(application=application)
        self.set_title("RGB Control")
        # Tamanho mais generoso e ergonômico
        self.set_default_size(550, 750)
        self.cpu_hex_label: Optional[Gtk.Label] = None # Inicialização segura

        
        logger.info("Carregando interface Libadwaita Premium...")
        self.backend = Backend()
        
        # Carregar CSS Global
        self.load_custom_css()
        
        # 1. ToolbarView (Root)
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)
        
        # 2. HeaderBar
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(Adw.WindowTitle(title="RGB Control", subtitle="Controle de Iluminação"))
        
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
        
        # Botão de visualização de logs (ícone de terminal)
        self.btn_logs = Gtk.Button()
        self.btn_logs.set_icon_name("utilities-terminal-symbolic")
        self.btn_logs.set_tooltip_text("Visualizar logs do sistema")
        self.btn_logs.connect("clicked", self.on_view_logs_clicked)
        self.header.pack_end(self.btn_logs)
        self.toolbar_view.add_top_bar(self.header)
        
        # 3. Conteúdo Principal com Clamp (Centralização Responsiva)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        clamp = Adw.Clamp()
        clamp.set_maximum_size(500) # Mantém os controles elegantes no centro
        clamp.set_tightening_threshold(400)
        clamp.set_hexpand(True)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        main_box.set_hexpand(True)
        main_box.set_margin_top(32)
        main_box.set_margin_bottom(32)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        
        # Tenta .svg diretamente
        logo_path = get_asset_path("logo.svg")
        if logo_path and os.path.exists(logo_path):
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
        self.switch_svc.set_title("Daemon de Captura (Background)")
        self.switch_svc.set_subtitle("Gerencia a escuta de eventos do Air Mouse")
        self.switch_svc.set_active(self.backend.is_service_active())
        self._svc_handler_id = self.switch_svc.connect("notify::active", self.on_service_notify)
        system_group.add(self.switch_svc)

        # Rótulo de status de conexão do controle remoto
        self.row_controller = Adw.ActionRow()
        self.row_controller.set_title("Controle Remoto (Air Mouse)")
        self.row_controller.set_subtitle("Buscando dispositivo...")
        self.row_controller.set_icon_name("accessory-controller-symbolic")

        self.label_controller_status = Gtk.Label(label="Buscando...")
        self.label_controller_status.set_valign(Gtk.Align.CENTER)
        self.label_controller_status.add_css_class("dim-label")
        self.row_controller.add_suffix(self.label_controller_status)
        system_group.add(self.row_controller)
        
        main_box.append(system_group)

        # Grupo 2: Controle Remoto (MODULAR)
        remote_group = Adw.PreferencesGroup()
        remote_group.set_title("Controle Remoto")
        remote_group.set_description("Gerencie a captura de botões do Air Mouse")

        self.switch_mode = Adw.SwitchRow()
        self.switch_mode.set_title("Ativar Captura Remota")
        self.switch_mode.set_subtitle("Permite mudar cores via ← → ou Vol±")
        self.switch_mode.set_active(self.backend.is_led_mode_active())
        self._mode_handler_id = self.switch_mode.connect("notify::active", self.on_mode_notify)
        remote_group.add(self.switch_mode)

        main_box.append(remote_group)
        
        # Grupo EXTRA: Cor Atual do CPU (Indicador Dinâmico)
        indicator_group = Adw.PreferencesGroup()
        indicator_group.set_title("Cor Atual do CPU")
        
        # Elementos visuais do indicador
        indicator_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        indicator_box.set_halign(Gtk.Align.CENTER)
        indicator_box.set_margin_top(16)
        indicator_box.set_margin_bottom(16)
        
        # Ventoinha Component Factory (Embutida e Animada)
        self.cpu_fan_overlay = Gtk.Overlay()
        self.cpu_fan_overlay.set_size_request(250, 250)
        self.cpu_fan_overlay.set_halign(Gtk.Align.CENTER)
        
        # O Motor central que girará!
        self.fan_spinner = Gtk.Overlay()
        self.fan_spinner.add_css_class("fan")
        
        # Resplendor/Brilho de fundo conectado na energia da Cor
        self.fan_glow = Gtk.Box()
        self.fan_glow.set_halign(Gtk.Align.FILL)
        self.fan_glow.set_valign(Gtk.Align.FILL)
        self.fan_glow.add_css_class("fan-glow")
        self.fan_spinner.add_overlay(self.fan_glow)
        
        # Pass (Hélices Mecânicas)
        b1 = Gtk.Box(); b1.add_css_class("blade"); b1.add_css_class("b1")
        b1.set_halign(Gtk.Align.CENTER); b1.set_valign(Gtk.Align.CENTER)
        self.fan_spinner.add_overlay(b1)
        
        b2 = Gtk.Box(); b2.add_css_class("blade"); b2.add_css_class("b2")
        b2.set_halign(Gtk.Align.CENTER); b2.set_valign(Gtk.Align.CENTER)
        self.fan_spinner.add_overlay(b2)
        
        b3 = Gtk.Box(); b3.add_css_class("blade"); b3.add_css_class("b3")
        b3.set_halign(Gtk.Align.CENTER); b3.set_valign(Gtk.Align.CENTER)
        self.fan_spinner.add_overlay(b3)
        
        # Eixo Central Escudo do Fan
        self.fan_hub = Gtk.Box()
        self.fan_hub.add_css_class("fan-hub")
        self.fan_hub.set_halign(Gtk.Align.CENTER)
        self.fan_hub.set_valign(Gtk.Align.CENTER)
        self.fan_hub.set_size_request(50, 50)
        
        # Montagem do chassi principal
        self.cpu_fan_overlay.set_child(self.fan_spinner)
        self.cpu_fan_overlay.add_overlay(self.fan_hub)
        
        indicator_box.append(self.cpu_fan_overlay)
        
        
        # Provedor CSS dinamico isolado para evitar recompilar TODO o estilo global
        self.cpu_css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.cpu_css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        indicator_row = Adw.ActionRow()
        indicator_row.set_activatable(False)
        indicator_row.set_child(indicator_box)
        indicator_group.add(indicator_row)
        
        main_box.append(indicator_group)
        
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
        
        # Adw.PreferencesGroup.add() aceita qualquer Gtk.Widget — mas para
        # garantir que o flowbox preencha corretamente, encapsulamos numa ActionRow
        palette_row = Adw.ActionRow()
        palette_row.set_activatable(False)
        # Centraliza e expande o flowbox dentro da row
        palette_box.set_hexpand(True)
        palette_box.set_valign(Gtk.Align.CENTER)
        palette_box.set_halign(Gtk.Align.CENTER)
        palette_row.set_child(palette_box)
        lighting_group.add(palette_row)
        
        main_box.append(lighting_group)
        main_box.append(custom_group)

        # Grupo 4: Ajuda e Instruções (Expander Row / Dropdown de manual)
        help_group = Adw.PreferencesGroup()
        help_group.set_title("Documentação e Ajuda")

        help_expander = Adw.ExpanderRow()
        help_expander.set_title("Manual do Controle Remoto")
        help_expander.set_subtitle("Lista de atalhos e botões mapeados")
        help_expander.set_icon_name("help-about-symbolic")

        help_btn_mic = Adw.ActionRow()
        help_btn_mic.set_title("🎙️ ou 🏠  (Microfone / Home)")
        help_btn_mic.set_subtitle("Liga / Desliga o MODO LED (Captura Remota)")
        help_expander.add_row(help_btn_mic)

        help_btn_next = Adw.ActionRow()
        help_btn_next.set_title("➡️ ou ➕ Vol+ (Seta Direita / Aumentar Volume)")
        help_btn_next.set_subtitle("Avança para a próxima cor da paleta")
        help_expander.add_row(help_btn_next)

        help_btn_prev = Adw.ActionRow()
        help_btn_prev.set_title("⬅️ ou ➖ Vol- (Seta Esquerda / Diminuir Volume)")
        help_btn_prev.set_subtitle("Retorna para a cor anterior da paleta")
        help_expander.add_row(help_btn_prev)

        help_btn_back = Adw.ActionRow()
        help_btn_back.set_title("↩️  Back (Botão Voltar)")
        help_btn_back.set_subtitle("Desativa o MODO LED e desliga a captura")
        help_expander.add_row(help_btn_back)

        help_group.add(help_expander)
        main_box.append(help_group)
        
        # Leitura da Versão embutida
        v_path = get_asset_path("version.txt")
        v_str = "v1.0.0"
        if v_path and os.path.exists(v_path):
            with open(v_path, "r") as f:
                v_str = f.read().strip()
                
        version_label = Gtk.Label(label=f"RGB Control • {v_str}")
        version_label.add_css_class("dim-label")
        version_label.set_margin_top(16)
        main_box.append(version_label)
        
        clamp.set_child(main_box)
        scrolled.set_child(clamp)
        self.toolbar_view.set_content(scrolled)
        
        self.setup_actions(application)
        GLib.timeout_add(2000, self.update_status_ui)
        
        # Inicializa o estado visual lendo o cache global do daemon na memoria
        startup_color = self.backend.get_current_color()
        self.update_cpu_indicator(startup_color)

    def update_cpu_indicator(self, hex_val: str) -> None:
        """Atualiza a Ventoinha 3D GTK com Glow Radiação do Fundo (Estética avançada)"""
        r, g, b, a = hex_to_rgba_tuple(hex_val)
        color_str = f"#{r:02X}{g:02X}{b:02X}"


            
        css = f"""
        .fan {{
            min-width: 75px; min-height: 75px;
            border-radius: 50%;
            background: radial-gradient(circle at center, rgba({r},{g},{b},0.95) 0%, rgba({int(r*0.2)},{int(g*0.2)},{int(b*0.2)},0.8) 100%);
            animation: spin 1s linear infinite;
        }}
        .fan-paused {{
            animation-play-state: paused;
        }}
        .fan-glow {{
            border-radius: 50%;
            background: radial-gradient(circle at center, rgba({r},{g},{b}, 0.5) 0%, rgba(0,0,0,0) 70%);
            opacity: 0.8;
        }}
        .fan-hub {{
            min-width: 50px; min-height: 50px;
            background: #fff;
            border-radius: 50%;
            border: 7px double {color_str};
            box-shadow: 0 0 10px rgba({r},{g},{b}, 0.8);
        }}
        .blade {{
            min-width: 100px; min-height: 50px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 25px;
            box-shadow: 0 0 15px rgba({r},{g},{b}, 0.6);
            transform-origin: 50% 50%;
        }}
        .b1 {{ transform: rotate(0deg) translate(75px, 0); }}
        .b2 {{ transform: rotate(120deg) translate(75px, 0); }}
        .b3 {{ transform: rotate(240deg) translate(75px, 0); }}
        
        @keyframes spin {{
            0%   {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        """
        self.cpu_css_provider.load_from_data(css.encode())
        
        if self.cpu_hex_label is not None:
            self.cpu_hex_label.set_markup(f"<span font_family='monospace' size='large' weight='bold'>{color_str.upper()}</span>")
        else:
            new_label = Gtk.Label()
            new_label.set_markup(f"<span font_family='monospace' size='large' weight='bold'>{color_str.upper()}</span>")
            new_label.add_css_class("dim-label")
            self.cpu_hex_label = new_label
            # Procura o overlay parent para append
            parent = self.cpu_fan_overlay.get_parent()
            if parent is not None:
                parent.append(self.cpu_hex_label)


    def load_custom_css(self) -> None:
        """Carrega o arquivo style.css — busca no mesmo dir do window.py e em assets/"""
        # Prioridade 1: mesmo diretório de window.py (src/rgb_control/style.css)
        own_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(own_dir, "style.css"),
            get_asset_path("style.css"),
        ]
        css_path = next((p for p in candidates if os.path.exists(p)), None)
        if css_path:
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            logger.info(f"CSS carregado de: {css_path}")
        else:
            logger.warning("style.css não encontrado — usando estilos inline apenas")

    def setup_actions(self, app: Gtk.Application) -> None:
        theme_light = Gio.SimpleAction.new("theme_light", None)
        theme_light.connect("activate", lambda a, p: Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT))
        app.add_action(theme_light)
        
        theme_dark = Gio.SimpleAction.new("theme_dark", None)
        theme_dark.connect("activate", lambda a,p: Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK))
        app.add_action(theme_dark)
        
        theme_system = Gio.SimpleAction.new("theme_system", None)
        theme_system.connect("activate", lambda a,p: Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.DEFAULT))
        app.add_action(theme_system)

    def on_service_notify(self, row: Adw.SwitchRow, param: Any) -> None:
        if self._updating_ui:
            return
        
        state = row.get_active()
        logger.info(f"Toggle Serviço solicitado: {state}")
        
        # Bloqueio estrito de reentrada durante a operação e possível reversão
        self._updating_ui = True
        try:
            success = self.backend.set_service_state(state)
            if not success:
                 logger.warning("Falha ao mudar estado do serviço no systemd")
                 self.switch_svc.handler_block(self._svc_handler_id)
                 row.set_active(not state)
                 self.switch_svc.handler_unblock(self._svc_handler_id)
        finally:
            self._updating_ui = False


    def on_mode_notify(self, row: Adw.SwitchRow, param: Any) -> None:
        if self._updating_ui:
            return
        state = row.get_active()
        logger.info(f"Toggle Modo solicitado: {state}")
        self.backend.set_led_mode(state)

    def on_color_clicked(self, widget: Gtk.Button, hex_val: str, name: str) -> None:
        logger.info(f"Cor predefinida escolhida: {name} ({hex_val})")
        self.update_cpu_indicator(hex_val)
        self.backend.apply_color(hex_val, name)

    def on_custom_color_selected(self, picker_btn: Gtk.ColorDialogButton, param: Any) -> None:
        rgba = picker_btn.get_rgba()
        r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        self.update_cpu_indicator(hex_val)
        self.backend.apply_color(hex_val, "Custom")

    def update_status_ui(self) -> bool:
        # Sincroniza estado UI -> Background sem disparar sinais recursivos
        try:
            svc_active = self.backend.is_service_active()
            mode_active = self.backend.is_led_mode_active()
            
            # Verifica se o controle remoto está fisicamente conectado
            ctrl_connected = self.backend.is_controller_connected()
            if ctrl_connected != self._last_ctrl_connected:
                self._last_ctrl_connected = ctrl_connected
                if ctrl_connected:
                    self.label_controller_status.set_label("Conectado")
                    self.label_controller_status.remove_css_class("dim-label")
                    self.label_controller_status.remove_css_class("error")
                    self.label_controller_status.add_css_class("success")
                    self.row_controller.set_subtitle("Receptor USB detectado no barramento")
                else:
                    self.label_controller_status.set_label("Desconectado")
                    self.label_controller_status.remove_css_class("dim-label")
                    self.label_controller_status.remove_css_class("success")
                    self.label_controller_status.add_css_class("error")
                    self.row_controller.set_subtitle("Controle desligado ou receptor USB ausente")

            self._updating_ui = True
            
            if self.switch_svc.get_active() != svc_active:
                logger.info(f"Sincronizando Switch Serviço para: {svc_active}")
                self.switch_svc.handler_block(self._svc_handler_id)
                self.switch_svc.set_active(svc_active)
                self.switch_svc.handler_unblock(self._svc_handler_id)
                
            # Interromper / Congelar visualmente a ventoinha se o serviço subjacente estiver desativado!
            if svc_active:
                if self.fan_spinner.has_css_class("fan-paused"):
                    self.fan_spinner.remove_css_class("fan-paused")
            else:
                if not self.fan_spinner.has_css_class("fan-paused"):
                    self.fan_spinner.add_css_class("fan-paused")
                
                
            if self.switch_mode.get_active() != mode_active:
                logger.info(f"Sincronizando Switch Modo para: {mode_active}")
                self.switch_mode.handler_block(self._mode_handler_id)
                self.switch_mode.set_active(mode_active)
                self.switch_mode.handler_unblock(self._mode_handler_id)
                
            self._updating_ui = False
        except Exception as e:
            logger.error(f"Erro na sincronização da UI: {e}")
            self._updating_ui = False
            
        return True

    def on_view_logs_clicked(self, button: Gtk.Button) -> None:
        """Abre o modal visualizador de logs"""
        log_window = LogViewerWindow(self, self.backend)
        log_window.present()


class LogViewerWindow(Adw.Window): # type: ignore[misc]
    def __init__(self, parent: Gtk.Window, backend: Backend) -> None:
        super().__init__(transient_for=parent, modal=True)
        self.set_title("Visualizador de Logs")
        self.set_default_size(650, 500)
        self.backend = backend
        
        # Conteúdo principal
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(box)
        
        # HeaderBar do modal
        header = Adw.HeaderBar()
        header.set_show_back_button(False)
        box.append(header)
        
        # Barra de ferramentas para controles
        control_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        control_bar.set_margin_start(12)
        control_bar.set_margin_end(12)
        control_bar.set_margin_top(8)
        control_bar.set_margin_bottom(8)
        
        # DropDown para seleção de logs
        self.dropdown = Gtk.DropDown.new_from_strings([
            "Log do Daemon (Background)",
            "Log do Aplicativo (GUI)"
        ])
        self.dropdown.connect("notify::selected", self.on_log_type_changed)
        control_bar.append(self.dropdown)
        
        # Espaçador
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        control_bar.append(spacer)
        
        # Botão Atualizar
        self.btn_refresh = Gtk.Button()
        self.btn_refresh.set_icon_name("view-refresh-symbolic")
        self.btn_refresh.set_tooltip_text("Atualizar logs")
        self.btn_refresh.connect("clicked", lambda b: self.refresh_logs())
        control_bar.append(self.btn_refresh)
        
        # Botão Copiar
        self.btn_copy = Gtk.Button()
        self.btn_copy.set_icon_name("edit-copy-symbolic")
        self.btn_copy.set_tooltip_text("Copiar para a área de transferência")
        self.btn_copy.connect("clicked", self.on_copy_clicked)
        control_bar.append(self.btn_copy)
        
        # Botão Limpar
        self.btn_clear = Gtk.Button()
        self.btn_clear.set_icon_name("user-trash-symbolic")
        self.btn_clear.set_tooltip_text("Limpar logs do arquivo")
        self.btn_clear.add_css_class("destructive-action")
        self.btn_clear.connect("clicked", self.on_clear_clicked)
        control_bar.append(self.btn_clear)
        
        box.append(control_bar)
        
        # TextView para exibição
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_margin_start(12)
        self.scrolled.set_margin_end(12)
        self.scrolled.set_margin_bottom(12)
        self.scrolled.add_css_class("card")
        
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_margin_top(8)
        self.text_view.set_margin_bottom(8)
        self.text_view.set_margin_start(8)
        self.text_view.set_margin_end(8)
        
        self.scrolled.set_child(self.text_view)
        box.append(self.scrolled)
        
        # Carregar logs
        self.refresh_logs()

    def get_selected_log_path(self) -> str:
        idx = self.dropdown.get_selected()
        if idx == 0:
            return self.backend.get_daemon_log_path()
        else:
            return self.backend.get_gui_log_path()

    def refresh_logs(self) -> None:
        path = self.get_selected_log_path()
        content = self.backend.read_log_file(path)
        
        buffer = self.text_view.get_buffer()
        buffer.set_text(content)
        
        # Rolar para o fim após o GTK renderizar
        GLib.idle_add(self.scroll_to_bottom)

    def scroll_to_bottom(self) -> bool:
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

    def on_log_type_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        self.refresh_logs()

    def on_copy_clicked(self, button: Gtk.Button) -> None:
        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True)
        
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(text)
        
        # Feedback visual
        button.set_icon_name("object-select-symbolic")
        GLib.timeout_add(1000, lambda: button.set_icon_name("edit-copy-symbolic") or False)

    def on_clear_clicked(self, button: Gtk.Button) -> None:
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Limpar Logs",
            body="Tem certeza que deseja apagar todo o conteúdo deste arquivo de log? Esta operação não pode ser desfeita."
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("clear", "Limpar")
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_attempt_response_id("cancel")
        
        def on_response(d: Adw.MessageDialog, response_id: str) -> None:
            if response_id == "clear":
                path = self.get_selected_log_path()
                self.backend.clear_log_file(path)
                self.refresh_logs()
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.present()
