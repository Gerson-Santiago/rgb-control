import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from rgb_daemon.infrastructure import NotifyOSD, OpenRGBColorApplicator, FileStatusStorage

class TestDaemonInfrastructure(unittest.TestCase):
    @patch('subprocess.run')
    def test_notify_osd_calls_command(self, mock_run):
        osd = NotifyOSD(user="testuser", dbus_addr="testbus")
        osd.notify("Title", "Body", urgency="low", icon="testicon")
        
        # Verify the command construction
        args = mock_run.call_args[0][0]
        self.assertIn("sudo", args)
        self.assertIn("testuser", args)
        self.assertIn("DBUS_SESSION_BUS_ADDRESS=testbus", args)
        self.assertIn("notify-send", args)
        self.assertIn("Title", args)
        self.assertIn("--urgency=low", args)
        self.assertIn("-i", args)
        self.assertIn("testicon", args)

    @patch('subprocess.run')
    def test_openrgb_applicator_success(self, mock_run):
        applicator = OpenRGBColorApplicator(device_id=0, user="testuser")
        mock_run.return_value.returncode = 0
        
        result = applicator.apply("FF0000", "Vermelho")
        
        self.assertTrue(result)
        args = mock_run.call_args[0][0]
        self.assertIn("openrgb", args)
        self.assertIn("0", args)
        self.assertIn("FF0000", args)

    @patch('subprocess.run')
    def test_openrgb_applicator_sudo_fallback(self, mock_run):
        applicator = OpenRGBColorApplicator(device_id=0, user="testuser")
        # First call (direct) fails, second call (sudo) succeeds
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]
        
        result = applicator.apply("FF0000", "Vermelho")
        
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)
        args = mock_run.call_args[0][0] # last call
        self.assertIn("sudo", args)
        self.assertIn("testuser", args)
        self.assertIn("openrgb", args)

    def test_file_status_storage(self):
        mock_status = MagicMock()
        mock_pid = MagicMock()
        storage = FileStatusStorage(mock_status, mock_pid)
        
        storage.save_status("on")
        mock_status.write_text.assert_called_with("on")
        
        storage.save_pid(1234)
        mock_pid.write_text.assert_called_with("1234")

if __name__ == '__main__':
    unittest.main()
