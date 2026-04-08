import unittest
import sys
import os
import signal
from unittest.mock import MagicMock, patch
from rgb_daemon.main import main, buscar_devices

class TestDaemonMainIntegration(unittest.TestCase):
    @patch('argparse.ArgumentParser.parse_args')
    @patch('rgb_daemon.main.buscar_devices')
    @patch('rgb_daemon.main.FileStatusStorage')
    @patch('rgb_daemon.main.run_daemon', new_callable=MagicMock)
    @patch('asyncio.run')
    def test_main_daemon_start(self, mock_run, mock_run_daemon, mock_storage, mock_search, mock_args):
        mock_args.return_value = MagicMock(toggle=False, status=False, list=False)
        mock_search.return_value = (MagicMock(), MagicMock())
        with patch('os.getpid', return_value=1234):
            main()
        mock_search.assert_called_once()
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('os.kill')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.read_text', return_value="1234")
    def test_main_cli_toggle(self, mock_read, mock_exists, mock_kill, mock_args):
        mock_args.return_value = MagicMock(toggle=True, status=False, list=False)
        main()
        mock_kill.assert_called_with(1234, signal.SIGUSR1)

    @patch('rgb_daemon.main.list_devices', return_value=['/dev/input/event0'])
    @patch('rgb_daemon.main.InputDevice')
    def test_buscar_devices_discovery(self, mock_device, mock_list):
        dev = mock_device.return_value
        dev.info.vendor = 0x1915
        dev.info.product = 0x1025
        dev.name = "Air Mouse Consumer Control"
        tecl, cons = buscar_devices()
        self.assertIsNotNone(cons)

    @patch('rgb_daemon.main.list_devices', return_value=[])
    def test_buscar_devices_empty(self, mock_list):
        tecl, cons = buscar_devices()
        self.assertIsNone(tecl)
        self.assertIsNone(cons)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('rgb_daemon.main.buscar_devices', return_value=(None, None))
    @patch('builtins.print')
    def test_main_cli_list(self, mock_print, mock_search, mock_args):
        mock_args.return_value = MagicMock(toggle=False, status=False, list=True)
        main()
        mock_search.assert_called_once()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('builtins.print')
    @patch('rgb_daemon.main.STATUS_FILE')
    def test_main_cli_status(self, mock_status_file, mock_print, mock_args):
        mock_args.return_value = MagicMock(toggle=False, status=True, list=False)
        mock_status_file.exists.return_value = True
        mock_status_file.read_text.return_value = "off"
        main()
        mock_print.assert_any_call("MODO LED: OFF")

if __name__ == '__main__':
    unittest.main()
