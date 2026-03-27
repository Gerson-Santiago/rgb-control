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

    @patch('subprocess.Popen')
    @patch('os.path.exists', return_value=True)
    def test_apply_color_script(self, mock_exists, mock_popen):
        # Mocking existence of rbg.sh
        self.backend.apply_color("FF0000", "Vermelho")
        mock_popen.assert_called()
        args = mock_popen.call_args[0][0]
        self.assertIn("bash", args)
        self.assertIn("vermelho", args)

    @patch('subprocess.Popen')
    @patch('os.path.exists', side_effect=lambda p: p == "/usr/bin/openrgb" or "openrgb" in p)
    def test_apply_color_fallback(self, mock_exists, mock_popen):
        # Mocking absence of rbg.sh and existence of openrgb
        with patch('os.path.exists', return_value=False):
            self.backend.apply_color("FF0000", "Vermelho")
            mock_popen.assert_called()
            args = mock_popen.call_args[0][0]
            self.assertIn("openrgb", args)

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
