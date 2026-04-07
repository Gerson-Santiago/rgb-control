import unittest
import os
import signal
from unittest.mock import MagicMock, patch, mock_open
from rgb_control.backend import Backend

class TestGuiBackend(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()

    @patch('subprocess.run')
    def test_is_service_active_true(self, mock_run):
        mock_run.return_value.stdout = "active\n"
        self.assertTrue(self.backend.is_service_active())

    @patch('subprocess.run')
    def test_is_service_active_exception(self, mock_run):
        mock_run.side_effect = Exception("error")
        self.assertFalse(self.backend.is_service_active())

    @patch('subprocess.run')
    def test_set_service_state_success(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.backend.set_service_state(True))

    @patch('subprocess.run')
    def test_set_service_state_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        self.assertFalse(self.backend.set_service_state(True))

    @patch('os.path.exists', return_value=True)
    def test_is_led_mode_active(self, mock_exists):
        with patch('builtins.open', mock_open(read_data="on")):
            self.assertTrue(self.backend.is_led_mode_active())
        with patch('builtins.open', mock_open(read_data="off")):
            self.assertFalse(self.backend.is_led_mode_active())

    @patch('builtins.open', new_callable=mock_open)
    def test_set_led_mode(self, mock_file):
        # Test basic write
        self.backend.set_led_mode(True)
        # Note: it opens /tmp/.controle_led.status
        mock_file().write.assert_called_with("on")

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data="1234"))
    @patch('os.kill')
    def test_set_led_mode_signals_daemon(self, mock_kill, mock_exists):
        # Test that it sends SIGUSR1 (10) to the PID in the file
        self.backend.set_led_mode(True)
        mock_kill.assert_called_with(1234, 10)

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
        self.backend.apply_color("000000", "Preto")
        
        # Popen DEVE ter sido acionado pelo fallback
        mock_popen.assert_called()
        args = mock_popen.call_args[0][0]
        self.assertIn("pkexec", args)
        self.assertIn("openrgb", args)
        self.assertIn("000000", args)

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data="line1\nline2\nline3\n"))
    def test_get_daemon_logs(self, mock_exists):
        logs = self.backend.get_daemon_logs(limit=2)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0], "line2")
        self.assertEqual(logs[1], "line3")

    @patch('os.path.exists', return_value=False)
    def test_get_daemon_logs_no_file(self, mock_exists):
        logs = self.backend.get_daemon_logs()
        self.assertEqual(logs, ["Arquivo de log não encontrado."])

if __name__ == '__main__':
    unittest.main()
