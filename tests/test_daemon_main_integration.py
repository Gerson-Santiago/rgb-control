import unittest
import sys
import os
import signal
from unittest.mock import MagicMock, patch, patch
from rgb_daemon.main import main, buscar_devices

class TestDaemonMainIntegration(unittest.TestCase):
    @patch('argparse.ArgumentParser.parse_args')
    @patch('rgb_daemon.main.buscar_devices')
    @patch('rgb_daemon.main.FileStatusStorage')
    @patch('asyncio.run')
    def test_main_daemon_start(self, mock_run, mock_storage, mock_search, mock_args):
        # Simula o início normal do daemon
        mock_args.return_value = MagicMock(toggle=False, status=False, list=False)
        mock_search.return_value = (MagicMock(), MagicMock())
        
        with patch('os.getpid', return_value=1234):
            main()
            
        mock_search.assert_called_once()
        mock_storage.return_value.save_pid.assert_called_with(1234)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('os.kill')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.read_text', return_value="1234")
    def test_main_cli_toggle(self, mock_read, mock_exists, mock_kill, mock_args):
        # Simula o comando --toggle enviando sinal para o processo existente
        mock_args.return_value = MagicMock(toggle=True, status=False, list=False)
        
        main()
        
        mock_kill.assert_called_with(1234, signal.SIGUSR1)

    @patch('evdev.list_devices', return_value=['/dev/input/event0'])
    @patch('evdev.InputDevice')
    def test_buscar_devices_discovery(self, mock_device, mock_list):
        # Simula a descoberta de um dispositivo compatível
        dev = mock_device.return_value
        dev.info.vendor = 0x1915
        dev.info.product = 0x1025
        dev.name = "Air Mouse Consumer Control"
        
        tecl, cons = buscar_devices()
        self.assertIsNotNone(cons)

if __name__ == '__main__':
    unittest.main()
