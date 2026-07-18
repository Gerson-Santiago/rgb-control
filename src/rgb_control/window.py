import gi # type: ignore[import-untyped]
import gi
import os
import logging
from typing import Optional, Any, Tuple, List, Union

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Gdk # type: ignore[import-untyped]
from rgb_control.backend import Backend
from rgb_control.log_viewer import LogViewerWindow

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
        super().__init__(application=application)
        self.set_title("RGB Control")
        # Tamanho mais compacto sem a ventoinha
        self.set_default_size(500, 520)

        
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

        # --- Grupos de Preferências (construídos por métodos especializados) ---

        # Paleta e cor personalizada (dois grupos separados)
        lighting_group, custom_group = self._build_lighting_groups()
        main_box.append(lighting_group)
        main_box.append(custom_group)

        main_box.append(self._build_extension_group())
        main_box.append(self._build_help_group())

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
        
        # Inicializa o estado visual lendo o cache global do daemon na memoria
        startup_color = self.backend.get_current_color()


    # ──────────────────────────────────────────────────────────────────────────
    # Construtores de grupos de preferências (Clean Code: __init__ enxuto)
    # ──────────────────────────────────────────────────────────────────────────





    def _build_lighting_groups(self) -> Tuple[Adw.PreferencesGroup, Adw.PreferencesGroup]:
        """Constrói o grupo da paleta de cores e o grupo de cor personalizada."""
        lighting_group = Adw.PreferencesGroup()
        lighting_group.set_title("Paleta de Cores")
        lighting_group.set_description("Selecione uma cor para aplicar instantaneamente")

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

        css_data = ""
        for _, hex_val in self.colors:
            cls = f"color-btn-{hex_val.strip('#')}"
            css_data += f".{cls} {{ background-color: {hex_val}; }}\n"

        provider = Gtk.CssProvider()
        provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        for name, hex_val in self.colors:
            btn = Gtk.Button()
            btn.add_css_class("color-btn")
            btn.add_css_class(f"color-btn-{hex_val.strip('#')}")
            btn.set_tooltip_text(name)
            btn.connect("clicked", self.on_color_clicked, hex_val, name)
            flowbox.insert(btn, -1)

        palette_box.append(flowbox)

        palette_row = Adw.ActionRow()
        palette_row.set_activatable(False)
        palette_box.set_hexpand(True)
        palette_box.set_valign(Gtk.Align.CENTER)
        palette_box.set_halign(Gtk.Align.CENTER)
        palette_row.set_child(palette_box)
        lighting_group.add(palette_row)

        # Grupo de cor personalizada (separado para destaque visual)
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

        return lighting_group, custom_group



    def _build_extension_group(self) -> Adw.PreferencesGroup:
        """Constrói o grupo de configuração dos 3 botões de cor rápida da extensão GNOME."""
        extension_group = Adw.PreferencesGroup()
        extension_group.set_title("Extensão GNOME (Barra Superior)")
        extension_group.set_description("Configure as 3 cores de acesso rápido exibidas no painel do GNOME")

        config = self.backend.get_extension_config()
        # Se for mock ou estrutura inválida
        if not isinstance(config, dict) or "quick_colors" not in config or len(config["quick_colors"]) < 3:
            try:
                config = self.backend.get_default_extension_config()
            except Exception:
                config = {}

        self.ext_pickers = []
        for i in range(3):
            row = Adw.ActionRow()
            row.set_title(f"Cor de Atalho {i + 1}")
            row.set_subtitle(f"Botão de cor {i + 1} no menu da extensão")

            color_hex = ""
            if isinstance(config, dict) and "quick_colors" in config and i < len(config["quick_colors"]):
                color_hex = config["quick_colors"][i].get("hex", "")

            # Se não for string válida, tenta ler do default do backend. Se falhar (mock), usa fallback estático estrito
            if not isinstance(color_hex, str) or not color_hex.startswith("#"):
                try:
                    default_colors = self.backend.get_default_extension_config()["quick_colors"]
                    color_hex = default_colors[i]["hex"]
                except Exception:
                    color_hex = ""

            if not isinstance(color_hex, str) or not color_hex.startswith("#"):
                color_hex = ["#FF5500", "#FF0000", "#0000FF"][i]

            picker = Gtk.ColorDialogButton()
            picker.set_dialog(self.color_dialog)
            picker.set_valign(Gtk.Align.CENTER)

            rgba = Gdk.RGBA()
            rgba.parse(color_hex)
            picker.set_rgba(rgba)

            picker.connect("notify::rgba", self.on_extension_color_changed, i)

            row.add_suffix(picker)
            extension_group.add(row)
            self.ext_pickers.append(picker)

        return extension_group

    def _build_help_group(self) -> Adw.PreferencesGroup:
        """Constrói o grupo de documentação e manual de atalhos do controle remoto."""
        help_group = Adw.PreferencesGroup()
        help_group.set_title("Documentação e Ajuda")

        help_expander = Adw.ExpanderRow()
        help_expander.set_title("Manual do Controle Remoto")
        help_expander.set_subtitle("Lista de atalhos e botões mapeados")
        help_expander.set_icon_name("help-about-symbolic")

        shortcuts: List[Tuple[str, str]] = [
            ("🎙️ ou 🏠  (Microfone / Home)", "Liga / Desliga o MODO LED (Captura Remota)"),
            ("➡️ ou ➕ Vol+ (Seta Direita / Aumentar Volume)", "Avança para a próxima cor da paleta"),
            ("⬅️ ou ➖ Vol- (Seta Esquerda / Diminuir Volume)", "Retorna para a cor anterior da paleta"),
            ("↩️  Back (Botão Voltar)", "Desativa o MODO LED e desliga a captura"),
        ]
        for title, subtitle in shortcuts:
            row = Adw.ActionRow()
            row.set_title(title)
            row.set_subtitle(subtitle)
            help_expander.add_row(row)

        help_group.add(help_expander)
        return help_group

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



    def on_color_clicked(self, widget: Gtk.Button, hex_val: str, name: str) -> None:
        logger.info(f"Cor predefinida escolhida: {name} ({hex_val})")
        self.backend.apply_color(hex_val, name)

    def on_custom_color_selected(self, picker_btn: Gtk.ColorDialogButton, param: Any) -> None:
        rgba = picker_btn.get_rgba()
        r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        self.backend.apply_color(hex_val, "Custom")

    def on_extension_color_changed(self, picker_btn: Gtk.ColorDialogButton, param: Any, index: int) -> None:
        rgba = picker_btn.get_rgba()
        r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        
        config = self.backend.get_extension_config()
        if not isinstance(config, dict) or "quick_colors" not in config or len(config["quick_colors"]) < 3:
            config = self.backend.get_default_extension_config()
            
        config["quick_colors"][index]["hex"] = hex_val
        config["quick_colors"][index]["name"] = self.get_color_name_from_hex(hex_val, f"Cor {index+1}")
        
        self.backend.save_extension_config(config)
        logger.info(f"Cor de atalho {index+1} da extensão GNOME alterada para {hex_val}")

    def get_color_name_from_hex(self, hex_val: str, default_name: str) -> str:
        mapping = {
            "#FF0000": "Vermelho",
            "#FF5500": "Laranja",
            "#FFFF00": "Amarelo",
            "#00FF00": "Verde",
            "#00F2EA": "Ciano",
            "#0000FF": "Azul",
            "#AA00FF": "Roxo",
            "#FFB200": "Ambar",
            "#FFFFFF": "Branco",
            "#000000": "Desativar"
        }
        return mapping.get(hex_val.upper(), default_name)



    def on_view_logs_clicked(self, button: Gtk.Button) -> None:
        """Abre o modal visualizador de logs"""
        log_window = LogViewerWindow(self, self.backend)
        log_window.present()
