# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
import signal
from unittest.mock import MagicMock, patch
from pathlib import Path
from rgb_daemon.main import handle_signal

class TestDaemonSignalSync(unittest.TestCase):
    def setUp(self):
        self.use_cases = MagicMock()
        self.stop_ev = MagicMock()
        self.status_file = MagicMock()

    def test_handle_sigusr1_syncs_from_file_on(self):
        """Valida que SIGUSR1 le 'on' do arquivo e ativa o daemon."""
        self.status_file.exists.return_value = True
        self.status_file.read_text.return_value = "on"
        
        handle_signal(signal.SIGUSR1, self.use_cases, None, self.status_file, self.stop_ev)
        
        self.use_cases.set_active.assert_called_once_with(True, None)

    def test_handle_sigusr1_syncs_from_file_off(self):
        """Valida que SIGUSR1 le 'off' do arquivo e desativa o daemon."""
        self.status_file.exists.return_value = True
        self.status_file.read_text.return_value = "off"
        
        handle_signal(signal.SIGUSR1, self.use_cases, None, self.status_file, self.stop_ev)
        
        self.use_cases.set_active.assert_called_once_with(False, None)

    def test_handle_sigint_stops_daemon(self):
        """Valida que SIGINT sinaliza a parada do daemon."""
        handle_signal(signal.SIGINT, self.use_cases, None, self.status_file, self.stop_ev)
        
        self.stop_ev.set.assert_called_once()

if __name__ == '__main__':
    unittest.main()
