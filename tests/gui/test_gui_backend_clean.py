# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
import os
import signal
from unittest.mock import MagicMock, patch, mock_open
from rgb_control.backend import Backend

class TestGuiBackend(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()



    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_apply_color_direct_success(self, mock_popen, mock_run):
        # Configura openrgb primário para sucesso (returncode 0)
        mock_run.return_value.returncode = 0
        self.backend.apply_color("FF0000", "Vermelho")
        
        # Verifica se chamou a via primária normal
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        self.assertIn("openrgb", args)
        self.assertNotIn("pkexec", args)
        
        # Como o código foi 0, NÃO deve ter acionado fallback
        mock_popen.assert_not_called()

    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_apply_color_direct_fallback_pkexec(self, mock_popen, mock_run):
        # Configura openrgb primário simulando bloqueio usb/udev (returncode 1)
        mock_run.return_value.returncode = 1
        self.backend.apply_color("FF0000", "Vermelho")
        
        # Popen DEVE ter sido acionado pelo fallback
        mock_popen.assert_called()
        args = mock_popen.call_args[0][0]
        self.assertIn("pkexec", args)
        self.assertIn("openrgb", args)
        self.assertIn("FF0000", args)



    def test_get_gui_log_path(self):
        self.assertTrue(self.backend.get_gui_log_path().endswith("app.log"))

    @patch('os.path.exists', return_value=True)
    def test_read_log_file_success(self, mock_exists):
        with patch('builtins.open', mock_open(read_data="test log data")):
            content = self.backend.read_log_file("/some/path.log")
            self.assertEqual(content, "test log data")

    @patch('os.path.exists', return_value=False)
    def test_read_log_file_not_found(self, mock_exists):
        content = self.backend.read_log_file("/some/path.log")
        self.assertIn("Arquivo de log não encontrado", content)

    @patch('os.path.exists', return_value=True)
    def test_read_log_file_error(self, mock_exists):
        with patch('builtins.open', side_effect=Exception("read error")):
            content = self.backend.read_log_file("/some/path.log")
            self.assertIn("Erro ao ler log", content)

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_clear_log_file_success(self, mock_file, mock_exists):
        success = self.backend.clear_log_file("/some/path.log")
        self.assertTrue(success)
        mock_file().write.assert_called_with("")

    @patch('os.path.exists', return_value=False)
    def test_clear_log_file_not_found(self, mock_exists):
        success = self.backend.clear_log_file("/some/path.log")
        self.assertFalse(success)

    @patch('os.path.exists', return_value=True)
    def test_clear_log_file_error(self, mock_exists):
        with patch('builtins.open', side_effect=Exception("write error")):
            success = self.backend.clear_log_file("/some/path.log")
            self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
