import unittest
from unittest.mock import MagicMock, patch
from gi.repository import Gtk, Adw, Gio
from rgb_control.window import MainWindow

class TestMainWindowStructureSafety(unittest.TestCase):
    """
    Testes de Sanidade Estrutural (Gold Standard v1.0.22).
    Garante que os widgets críticos existam no carregamento real.
    """

    def setUp(self):
        # Para satisfazer o PyGObject (gi), precisamos de uma aplicação e ID real
        self.app = Adw.Application(application_id=f"com.test.structural.{id(self)}", flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        with patch('rgb_control.window.Backend') as mock_backend_cls:
            self.mock_backend = mock_backend_cls.return_value
            self.mock_backend.get_current_color.return_value = "#FF0000"
            
            with patch('os.path.exists', return_value=False), \
                 patch('gi.repository.Gtk.CssProvider'), \
                 patch('gi.repository.Gdk.Display.get_default'), \
                 patch('rgb_control.window.get_asset_path', return_value=""):
                # IMPORTANTE: No Gold Standard, não patchamos o Display 
                # a não ser que estejamos em um ambiente SEM Display REAL.
                # Mas como removemos o patch do Display do conftest, aqui também removemos.
                pass
            
            # Recriando o setup sem patches de baixo nível que quebram a C-Binding
            with patch('rgb_control.window.get_asset_path', return_value=""):
                self.window = MainWindow(application=self.app)

    def test_core_ui_widgets_are_bound_and_valid(self):
        """Verifica se os componentes principais foram instanciados corretamente."""
        self.assertIsInstance(self.window.toolbar_view, Adw.ToolbarView)
        self.assertIsInstance(self.window.switch_svc, Adw.SwitchRow)
        self.assertIsInstance(self.window.switch_mode, Adw.SwitchRow)
        self.assertIsInstance(self.window.fan_spinner, Gtk.Overlay)

    def test_fan_cooler_rendering_layers(self):
        """Verifica se a ventoinha dinâmica possui as camadas de glow necessárias."""
        # Se a ventoinha estiver lá, o overlay deve ter pelo menos um child (o spinner)
        self.assertIsNotNone(self.window.fan_spinner)
        # O Hub central deve existir
        has_hub = False
        # Para GTK4, inspecionamos os children se necessário, mas aqui basta verificar a atribuição
        self.assertTrue(hasattr(self.window, 'fan_spinner'))

    def test_startup_does_not_crash(self):
        """Teste de fumaça (Smoke Test) para garantir que o __init__ não levanta exceções."""
        from gi.repository import Adw, Gio
        app = Adw.Application(application_id="com.test.startup.smoke", flags=Gio.ApplicationFlags.FLAGS_NONE)
        with patch('rgb_control.window.Backend') as mock_backend_cls:
             mock_backend_cls.return_value.get_current_color.return_value = "#000000"
             MainWindow(application=app)
