import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Setup PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import from the new src/ layout
from rgb_control.backend import Backend

class TestBackend(unittest.TestCase):
    @patch('subprocess.run')
    def test_service_status_parsing(self, mock_run):
        """Verifica se o backend interpreta corretamente o output do systemctl"""
        backend = Backend()
        
        # Simula serviço ativo
        mock_run.return_value.stdout = "active\n"
        self.assertTrue(backend.is_service_active())
        
        # Simula serviço inativo
        mock_run.return_value.stdout = "inactive\n"
        self.assertFalse(backend.is_service_active())

    @patch('subprocess.run')
    def test_service_control_commands(self, mock_run):
        """Verifica se os comandos pkexec + systemctl são montados corretamente"""
        backend = Backend()
        mock_run.return_value.returncode = 0
        
        backend.set_service_state(True)
        # O comando real agora usa pkexec para privilégios de root
        mock_run.assert_called_with(["pkexec", "systemctl", "start", "openrbg.service"], capture_output=True)
        
        backend.set_service_state(False)
        mock_run.assert_called_with(["pkexec", "systemctl", "stop", "openrbg.service"], capture_output=True)

    @patch('os.path.exists', return_value=True)
    def test_led_mode_status(self, mock_exists):
        """Verifica se o status do modo LED (on/off) é lido corretamente de /tmp"""
        backend = Backend()
        
        # Simula o arquivo de status contendo 'on'
        with patch('builtins.open', unittest.mock.mock_open(read_data="on")):
            self.assertTrue(backend.is_led_mode_active())
            
        # Simula o arquivo de status contendo 'off'
        with patch('builtins.open', unittest.mock.mock_open(read_data="off")):
            self.assertFalse(backend.is_led_mode_active())

if __name__ == '__main__':
    unittest.main()
