# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
"""
Testes unitários para rgb_control.log_viewer.LogViewerWindow.

Após a refatoração SRP (Single Responsibility Principle), o LogViewerWindow
foi extraído de window.py para seu próprio módulo log_viewer.py.
Estes testes garantem que todas as responsabilidades do módulo estão cobertas:
    - Inicialização e widgets
    - Seleção de fonte de log (Daemon vs GUI)
    - Refresh manual e auto-refresh
    - Copiar para clipboard
    - Limpar arquivo de log (com confirmação)
    - Cleanup do timeout no destroy
"""
import unittest
from unittest.mock import MagicMock, patch
from gi.repository import Gtk, Adw, Gio

from rgb_control.log_viewer import LogViewerWindow
from rgb_control.window import MainWindow


class TestLogViewerWindowBase(unittest.TestCase):
    """
    Base com setup compartilhado: cria MainWindow e LogViewerWindow com backend mockado.
    """

    def setUp(self) -> None:
        self.app = Adw.Application(
            application_id=f"com.test.logviewer.unit.{id(self)}",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.mock_backend = MagicMock()
        self.mock_backend.get_current_color.return_value = "#FF0000"
        self.mock_backend.get_daemon_log_path.return_value = "/tmp/mock-daemon.log"
        self.mock_backend.get_gui_log_path.return_value = "/tmp/mock-gui.log"
        self.mock_backend.read_log_file.return_value = "linha 1\nlinha 2\nlinha 3"

        with patch("rgb_control.window.get_asset_path", return_value=""):
            self.main_win = MainWindow(application=self.app)

        self.log_win = LogViewerWindow(
            parent=self.main_win, backend=self.mock_backend
        )

    def tearDown(self) -> None:
        if hasattr(self.log_win, "_refresh_timeout_id") and self.log_win._refresh_timeout_id:
            with patch("gi.repository.GLib.source_remove"):
                self.log_win.on_destroy(None)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Estrutura e inicialização
# ──────────────────────────────────────────────────────────────────────────────

class TestLogViewerWidgets(TestLogViewerWindowBase):
    """Verifica a estrutura dos widgets após a inicialização."""

    def test_lbl_title_is_gtk_label(self) -> None:
        self.assertIsInstance(self.log_win.lbl_title, Gtk.Label)

    def test_btn_refresh_is_gtk_button(self) -> None:
        self.assertIsInstance(self.log_win.btn_refresh, Gtk.Button)

    def test_btn_copy_is_gtk_button(self) -> None:
        self.assertIsInstance(self.log_win.btn_copy, Gtk.Button)

    def test_btn_clear_is_gtk_button(self) -> None:
        self.assertIsInstance(self.log_win.btn_clear, Gtk.Button)

    def test_text_view_is_monospace_and_non_editable(self) -> None:
        tv = self.log_win.text_view
        self.assertIsInstance(tv, Gtk.TextView)
        self.assertFalse(tv.get_editable())
        self.assertTrue(tv.get_monospace())

    def test_scrolled_window_is_present(self) -> None:
        self.assertIsInstance(self.log_win.scrolled, Gtk.ScrolledWindow)

    def test_window_title_is_correct(self) -> None:
        self.assertEqual(self.log_win.get_title(), "Visualizador de Logs")

    def test_auto_refresh_timeout_is_registered(self) -> None:
        """O ID do timeout do auto-refresh deve ser um inteiro positivo."""
        self.assertIsInstance(self.log_win._refresh_timeout_id, int)
        self.assertGreater(self.log_win._refresh_timeout_id, 0)

    def test_btn_clear_has_destructive_action_class(self) -> None:
        self.assertIn("destructive-action", self.log_win.btn_clear.get_css_classes())





# ──────────────────────────────────────────────────────────────────────────────
# 3. Refresh de logs
# ──────────────────────────────────────────────────────────────────────────────

class TestLogViewerRefresh(TestLogViewerWindowBase):

    def test_refresh_logs_calls_backend_read(self) -> None:
        self.mock_backend.read_log_file.reset_mock()
        self.log_win.refresh_logs()
        self.mock_backend.read_log_file.assert_called_once()

    def test_refresh_logs_populates_text_buffer(self) -> None:
        self.log_win.refresh_logs()
        buffer = self.log_win.text_view.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True)
        self.assertIn("linha 1", text)
        self.assertIn("linha 3", text)




# ──────────────────────────────────────────────────────────────────────────────
# 4. Auto-refresh
# ──────────────────────────────────────────────────────────────────────────────

class TestLogViewerAutoRefresh(TestLogViewerWindowBase):

    @patch("gi.repository.GLib.idle_add")
    def test_auto_refresh_returns_true_to_keep_timer_alive(self, mock_idle: MagicMock) -> None:
        result = self.log_win.auto_refresh_logs()
        self.assertTrue(result)

    @patch("gi.repository.GLib.idle_add")
    def test_auto_refresh_no_update_when_content_unchanged(self, mock_idle: MagicMock) -> None:
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("linha 1\nlinha 2\nlinha 3")
        self.log_win.auto_refresh_logs()
        mock_idle.assert_not_called()

    @patch("gi.repository.GLib.idle_add")
    def test_auto_refresh_updates_buffer_when_content_changes(self, mock_idle: MagicMock) -> None:
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("conteúdo antigo")
        self.log_win.auto_refresh_logs()
        start, end = buffer.get_bounds()
        new_text = buffer.get_text(start, end, True)
        self.assertEqual(new_text, "linha 1\nlinha 2\nlinha 3")

    @patch("gi.repository.GLib.idle_add")
    def test_auto_refresh_scrolls_when_user_is_at_bottom(self, mock_idle: MagicMock) -> None:
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("conteúdo antigo")
        adj = self.log_win.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        self.log_win.auto_refresh_logs()
        mock_idle.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# 5. Copiar para clipboard
# ──────────────────────────────────────────────────────────────────────────────

class TestLogViewerCopy(TestLogViewerWindowBase):

    @patch("gi.repository.Gdk.Display.get_default")
    def test_copy_sends_full_buffer_text_to_clipboard(self, mock_get_default: MagicMock) -> None:
        mock_clipboard = MagicMock()
        mock_get_default.return_value.get_clipboard.return_value = mock_clipboard
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("linha 1\nlinha 2\nlinha 3")
        self.log_win.on_copy_clicked(self.log_win.btn_copy)
        mock_clipboard.set_text.assert_called_once_with("linha 1\nlinha 2\nlinha 3")

    @patch("gi.repository.GLib.timeout_add")
    @patch("gi.repository.Gdk.Display.get_default")
    def test_copy_changes_icon_temporarily(self, mock_get_default: MagicMock, mock_timeout: MagicMock) -> None:
        mock_get_default.return_value.get_clipboard.return_value = MagicMock()
        self.log_win.on_copy_clicked(self.log_win.btn_copy)
        self.assertEqual(self.log_win.btn_copy.get_icon_name(), "object-select-symbolic")
        mock_timeout.assert_called()

    @patch("gi.repository.Gdk.Display.get_default")
    def test_copy_with_empty_buffer(self, mock_get_default: MagicMock) -> None:
        mock_clipboard = MagicMock()
        mock_get_default.return_value.get_clipboard.return_value = mock_clipboard
        buffer = self.log_win.text_view.get_buffer()
        buffer.set_text("")
        self.log_win.on_copy_clicked(self.log_win.btn_copy)
        mock_clipboard.set_text.assert_called_once_with("")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Limpar arquivo de log
# ──────────────────────────────────────────────────────────────────────────────

class TestLogViewerClear(TestLogViewerWindowBase):

    @patch("gi.repository.Adw.MessageDialog")
    def test_clear_shows_confirmation_dialog(self, mock_dialog_cls: MagicMock) -> None:
        mock_dialog = mock_dialog_cls.return_value
        self.log_win.on_clear_clicked(self.log_win.btn_clear)
        mock_dialog_cls.assert_called_once()
        mock_dialog.present.assert_called_once()

    @patch("gi.repository.Adw.MessageDialog")
    def test_clear_does_not_call_backend_without_confirmation(self, mock_dialog_cls: MagicMock) -> None:
        self.log_win.on_clear_clicked(self.log_win.btn_clear)
        self.mock_backend.clear_log_file.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# 7. Destroy / cleanup do timer
# ──────────────────────────────────────────────────────────────────────────────

class TestLogViewerDestroy(TestLogViewerWindowBase):

    def test_on_destroy_removes_timeout(self) -> None:
        self.log_win._refresh_timeout_id = 42
        with patch("gi.repository.GLib.source_remove") as mock_remove:
            self.log_win.on_destroy(None)
            mock_remove.assert_called_once_with(42)

    def test_on_destroy_sets_timeout_id_to_none(self) -> None:
        self.log_win._refresh_timeout_id = 99
        with patch("gi.repository.GLib.source_remove"):
            self.log_win.on_destroy(None)
        self.assertIsNone(self.log_win._refresh_timeout_id)

    def test_on_destroy_is_safe_when_no_timeout(self) -> None:
        self.log_win._refresh_timeout_id = None
        with patch("gi.repository.GLib.source_remove") as mock_remove:
            try:
                self.log_win.on_destroy(None)
            except Exception as e:
                self.fail(f"on_destroy crashou sem timeout registrado: {e}")
            mock_remove.assert_not_called()

    def test_on_destroy_is_idempotent(self) -> None:
        self.log_win._refresh_timeout_id = 55
        with patch("gi.repository.GLib.source_remove"):
            self.log_win.on_destroy(None)
            self.log_win.on_destroy(None)


# ──────────────────────────────────────────────────────────────────────────────
# 8. Backend — métodos de I/O de log
# ──────────────────────────────────────────────────────────────────────────────

class TestBackendLogMethods(unittest.TestCase):
    """
    Testes unitários dos métodos de infraestrutura do Backend usados pelo LogViewerWindow.
    """

    def setUp(self) -> None:
        from rgb_control.backend import Backend
        self.backend = Backend()

    def test_read_log_file_returns_not_found_for_missing_file(self) -> None:
        result = self.backend.read_log_file("/tmp/arquivo-que-nao-existe-xyz.log")
        self.assertIn("não encontrado", result)

    def test_read_log_file_returns_content_for_existing_file(self) -> None:
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("entrada de log de teste\n")
            tmp_path = f.name
        try:
            result = self.backend.read_log_file(tmp_path)
            self.assertIn("entrada de log de teste", result)
        finally:
            os.unlink(tmp_path)

    def test_clear_log_file_truncates_existing_file(self) -> None:
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("dados que devem ser apagados\n")
            tmp_path = f.name
        try:
            result = self.backend.clear_log_file(tmp_path)
            self.assertTrue(result)
            with open(tmp_path) as f:
                self.assertEqual(f.read(), "")
        finally:
            os.unlink(tmp_path)

    def test_clear_log_file_returns_false_for_missing_file(self) -> None:
        result = self.backend.clear_log_file("/tmp/nao-existe-abc123.log")
        self.assertFalse(result)



    def test_get_gui_log_path_returns_nonempty_string_with_rgb_control(self) -> None:
        path = self.backend.get_gui_log_path()
        self.assertIsInstance(path, str)
        self.assertIn("rgb-control", path)
