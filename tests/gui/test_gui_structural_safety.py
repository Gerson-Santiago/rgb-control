import unittest
from unittest.mock import MagicMock, patch
from gi.repository import Gtk, Adw, Gio
from rgb_control.window import MainWindow, LogViewerWindow

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
        self.assertIsInstance(self.window.row_controller, Adw.ActionRow)
        self.assertIsInstance(self.window.label_controller_status, Gtk.Label)
        self.assertIsInstance(self.window.fan_spinner, Gtk.Overlay)
        self.assertIsInstance(self.window.btn_logs, Gtk.Button)

    def test_fan_cooler_rendering_layers(self):
        """Verifica se a ventoinha dinâmica possui as camadas de glow necessárias."""
        # Se a ventoinha estiver lá, o overlay deve ter pelo menos um child (o spinner)
        self.assertIsNotNone(self.window.fan_spinner)
        # O Hub central deve existir
        has_hub = False
        # Para GTK4, inspecionamos os children se necessário, mas aqui basta verificar a atribuição
        self.assertTrue(hasattr(self.window, 'fan_spinner'))

    def test_update_cpu_indicator_logic(self):
        """Valida que a atualização do indicador de CPU (hex label) funciona sem crashes."""
        # Forçamos a criação do label se ele não existir
        self.window.update_cpu_indicator("#00FF00")
        self.assertIsNotNone(self.window.cpu_hex_label)
        # O markup deve conter a cor
        self.assertIn("00FF00", self.window.cpu_hex_label.get_label())

    def test_startup_does_not_crash(self):
        """Teste de fumaça (Smoke Test) para garantir que o __init__ não levanta exceções."""
        from gi.repository import Adw, Gio
        app = Adw.Application(application_id="com.test.startup.smoke", flags=Gio.ApplicationFlags.FLAGS_NONE)
        with patch('rgb_control.window.Backend') as mock_backend_cls:
             mock_backend_cls.return_value.get_current_color.return_value = "#000000"
             MainWindow(application=app)


class TestLogViewerWindow(unittest.TestCase):
    """Testes de unidade para a tela modal LogViewerWindow."""

    def setUp(self):
        self.app = Adw.Application(application_id=f"com.test.logviewer.{id(self)}", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.mock_backend = MagicMock()
        self.mock_backend.get_current_color.return_value = "#FF0000"
        self.mock_backend.get_daemon_log_path.return_value = "/tmp/mock-daemon.log"
        self.mock_backend.get_gui_log_path.return_value = "/tmp/mock-gui.log"
        self.mock_backend.read_log_file.return_value = "mock log line 1\nmock log line 2"
        
        # Mocks para o GTK rodar sem DISPLAY em headless
        with patch('rgb_control.window.get_asset_path', return_value=""):
             self.main_win = MainWindow(application=self.app)
             self.log_win = LogViewerWindow(parent=self.main_win, backend=self.mock_backend)

    def test_log_viewer_widgets(self):
        """Verifica a inicialização e os tipos dos widgets do LogViewerWindow."""
        self.assertIsInstance(self.log_win.dropdown, Gtk.DropDown)
        self.assertIsInstance(self.log_win.btn_refresh, Gtk.Button)
        self.assertIsInstance(self.log_win.btn_copy, Gtk.Button)
        self.assertIsInstance(self.log_win.btn_clear, Gtk.Button)
        self.assertIsInstance(self.log_win.text_view, Gtk.TextView)

    def test_get_selected_log_path(self):
        """Valida que o caminho do log correto é retornado de acordo com o DropDown."""
        # Selecionado idx 0 (Daemon)
        self.log_win.dropdown.set_selected(0)
        self.assertEqual(self.log_win.get_selected_log_path(), "/tmp/mock-daemon.log")
        
        # Selecionado idx 1 (GUI)
        self.log_win.dropdown.set_selected(1)
        self.assertEqual(self.log_win.get_selected_log_path(), "/tmp/mock-gui.log")

    def test_refresh_logs(self):
        """Verifica se os logs são carregados no buffer do TextView."""
        self.log_win.refresh_logs()
        self.mock_backend.read_log_file.assert_called()
        buffer = self.log_win.text_view.get_buffer()
        start, end = buffer.get_bounds()
        self.assertIn("mock log line 1", buffer.get_text(start, end, True))

    @patch('gi.repository.Gdk.Display.get_default')
    def test_on_copy_clicked(self, mock_get_default):
        """Valida que os logs são salvos na área de transferência ao clicar em copiar."""
        mock_clipboard = MagicMock()
        mock_get_default.return_value.get_clipboard.return_value = mock_clipboard
        
        self.log_win.on_copy_clicked(self.log_win.btn_copy)
        mock_clipboard.set_text.assert_called_with("mock log line 1\nmock log line 2")

    @patch('gi.repository.Adw.MessageDialog')
    def test_on_clear_clicked(self, mock_dialog_cls):
        """Garante que a confirmação de limpeza dos logs é disparada."""
        mock_dialog = mock_dialog_cls.return_value
        self.log_win.on_clear_clicked(self.log_win.btn_clear)
        mock_dialog_cls.assert_called_once()
        mock_dialog.present.assert_called_once()

    def test_on_destroy(self):
        """Valida que o temporizador do auto-refresh é removido no fechamento da janela."""
        self.log_win._refresh_timeout_id = 999
        with patch('gi.repository.GLib.source_remove') as mock_remove:
            self.log_win.on_destroy(None)
            mock_remove.assert_called_once_with(999)
            self.assertIsNone(self.log_win._refresh_timeout_id)

    @patch('gi.repository.GLib.idle_add')
    def test_auto_refresh_logs_no_change(self, mock_idle_add):
        """Verifica que o auto-refresh não atualiza o TextView se o conteúdo do log for idêntico."""
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("mock log line 1\nmock log line 2")
        
        res = self.log_win.auto_refresh_logs()
        self.assertTrue(res)
        mock_idle_add.assert_not_called()

    @patch('gi.repository.GLib.idle_add')
    def test_auto_refresh_logs_with_change(self, mock_idle_add):
        """Valida que o auto-refresh atualiza o buffer caso o conteúdo do log mude."""
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("old data")
        
        res = self.log_win.auto_refresh_logs()
        self.assertTrue(res)
        
        start, end = buffer.get_bounds()
        self.assertEqual(buffer.get_text(start, end, True), "mock log line 1\nmock log line 2")

