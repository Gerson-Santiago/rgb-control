import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
try:
    from rgb_control.backend import Backend
except ImportError:
    from backend import Backend

def get_asset_path(filename):
    """Retorna o caminho do asset, buscando localmente ou na estrutura do .deb"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_path = os.path.join(base_dir, filename)
    if os.path.exists(local_path):
        return local_path
    return os.path.join('/usr/share/rgb-control', filename)

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)
        self.set_title("RGB Control")
        self.set_default_size(500, 650)
        
        self.backend = Backend()
        
        # HeaderBar with Window Controls
        self.header = Adw.HeaderBar()
        self.header.set_decoration_layout("menu:minimize,maximize,close")

        # Config/Theme Menu
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
        
        # Main Layout Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        
        # Content Scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Logo Display
        logo_path = get_asset_path("logo.svg")
        try:
            self.logo = Gtk.Picture.new_for_filename(logo_path)
            self.logo.set_size_request(-1, 100)
            self.logo.set_content_fit(Gtk.ContentFit.CONTAIN)
            content_box.append(self.logo)
        except Exception:
            pass
            
        # Preferences Group (Daemon Control)
        daemon_group = Adw.PreferencesGroup()
        daemon_group.set_title("Configurações do Serviço")
        
        row_svc = Adw.ActionRow()
        row_svc.set_title("Serviço OpenRBG (Background)")
        row_svc.set_subtitle("Gerencia o daemon do Air Mouse via systemctl")
        self.switch_svc = Gtk.Switch()
        self.switch_svc.set_valign(Gtk.Align.CENTER)
        self.switch_svc.set_active(self.backend.is_service_active())
        self.switch_svc.connect("state-set", self.on_service_toggle)
        row_svc.add_suffix(self.switch_svc)
        daemon_group.add(row_svc)
        
        row_mode = Adw.ActionRow()
        row_mode.set_title("Modo LED Ativo")
        row_mode.set_subtitle("Ativar a captura das teclas do controle remoto")
        self.switch_mode = Gtk.Switch()
        self.switch_mode.set_valign(Gtk.Align.CENTER)
        self.switch_mode.set_active(self.backend.is_led_mode_active())
        self.switch_mode.connect("state-set", self.on_mode_toggle)
        row_mode.add_suffix(self.switch_mode)
        daemon_group.add(row_mode)
        
        content_box.append(daemon_group)
        
        # Color Grid (Paleta Padrão)
        color_group = Adw.PreferencesGroup()
        color_group.set_title("Paleta de Cores")
        
        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_max_children_per_line(5)
        flowbox.set_row_spacing(10)
        flowbox.set_column_spacing(10)
        
        # Mesma paleta do mvp.py
        self.colors = [
            ("Vermelho", "#FF0000"), ("Laranja", "#FF5500"), ("Amarelo", "#FFFF00"),
            ("Verde", "#00FF00"), ("Ciano", "#00F2EA"), ("Azul", "#0000FF"),
            ("Roxo", "#AA00FF"), ("Ambar", "#FFB200"), ("Branco", "#FFFFFF"),
            ("Desligar", "#000000")
        ]
        
        for name, hex_val in self.colors:
            btn = Gtk.Button()
            btn.set_width_request(45)
            btn.set_height_request(45)
            btn.set_tooltip_text(name)
            
            context = btn.get_style_context()
            provider = Gtk.CssProvider()
            css = f"button {{ background-color: {hex_val}; border-radius: 22px; }}"
            # Add border if it's black to be visible in dark mode
            if hex_val == "#000000":
                css = f"button {{ background-color: {hex_val}; border-radius: 22px; border: 1px solid #777; }}"
            provider.load_from_data(css.encode())
            context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            btn.connect("clicked", self.on_color_clicked, hex_val, name)
            flowbox.insert(btn, -1)
            
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        color_box.set_halign(Gtk.Align.CENTER)
        color_box.append(flowbox)
        color_group.add(color_box)
        
        content_box.append(color_group)
        
        # Color Picker Customizado
        custom_group = Adw.PreferencesGroup()
        custom_group.set_title("Cor Personalizada")
        
        self.color_dialog = Gtk.ColorDialog()
        picker_btn = Gtk.ColorDialogButton()
        picker_btn.set_dialog(self.color_dialog)
        picker_btn.set_halign(Gtk.Align.CENTER)
        picker_btn.connect("notify::rgba", self.on_custom_color_selected)
        
        custom_group.add(picker_btn)
        content_box.append(custom_group)
        
        scrolled.set_child(content_box)
        main_box.append(scrolled)
        self.set_content(main_box)
        
        self.setup_actions(application)
        
        # Start state checker
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

    def on_service_toggle(self, switch, state):
        success = self.backend.set_service_state(state)
        if not success:
            # Reverte estado se falhar ao usar o pkexec
            return True
        return False

    def on_mode_toggle(self, switch, state):
        self.backend.set_led_mode(state)
        return False

    def on_color_clicked(self, widget, hex_val, name):
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
