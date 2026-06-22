import unittest
from unittest.mock import patch, MagicMock
from rgb_control.backend import Backend

class TestControllerIntegration(unittest.TestCase):
    """
    Testa o método is_controller_connected do backend
    simulando diferentes cenários no barramento evdev.
    """

    def setUp(self):
        self.backend = Backend()

    @patch('evdev.list_devices')
    @patch('evdev.InputDevice')
    def test_controller_connected_success(self, mock_input_device, mock_list_devices):
        """Valida que o método retorna True quando o Air Mouse (1915:1025) está na lista."""
        mock_list_devices.return_value = ['/dev/input/event10']
        
        # Mock do dispositivo correspondente
        mock_dev = MagicMock()
        mock_dev.info.vendor = 0x1915
        mock_dev.info.product = 0x1025
        mock_input_device.return_value = mock_dev
        
        connected = self.backend.is_controller_connected()
        self.assertTrue(connected)
        mock_input_device.assert_called_once_with('/dev/input/event10')

    @patch('evdev.list_devices')
    @patch('evdev.InputDevice')
    def test_controller_disconnected(self, mock_input_device, mock_list_devices):
        """Valida que o método retorna False quando o Air Mouse não está na lista."""
        mock_list_devices.return_value = ['/dev/input/event1']
        
        # Mock de outro dispositivo qualquer (ex: teclado padrão)
        mock_dev = MagicMock()
        mock_dev.info.vendor = 0x9999
        mock_dev.info.product = 0x9999
        mock_input_device.return_value = mock_dev
        
        connected = self.backend.is_controller_connected()
        self.assertFalse(connected)

    @patch('evdev.list_devices')
    @patch('evdev.InputDevice')
    def test_controller_read_exception_resilience(self, mock_input_device, mock_list_devices):
        """Valida que o método é resiliente a exceções ao ler dispositivos protegidos ou inválidos."""
        mock_list_devices.return_value = ['/dev/input/event0', '/dev/input/event10']
        
        # event0 levanta permissão negada, event10 retorna o controle conectado
        def side_effect(path):
            if path == '/dev/input/event0':
                raise PermissionError("Permission denied")
            mock_dev = MagicMock()
            mock_dev.info.vendor = 0x1915
            mock_dev.info.product = 0x1025
            return mock_dev
            
        mock_input_device.side_effect = side_effect
        
        connected = self.backend.is_controller_connected()
        # O loop deve ignorar a exceção do event0 e encontrar o controle no event10
        self.assertTrue(connected)
