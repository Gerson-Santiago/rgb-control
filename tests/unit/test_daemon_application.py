import unittest
from unittest.mock import MagicMock, patch
from rgb_daemon.domain import DaemonState, Color
from rgb_daemon.application import DaemonUseCases

class TestDaemonApplication(unittest.TestCase):
    def setUp(self):
        self.state = DaemonState()
        self.mock_osd = MagicMock()
        self.mock_applicator = MagicMock()
        self.mock_storage = MagicMock()
        self.use_cases = DaemonUseCases(
            self.state, self.mock_osd, self.mock_applicator, self.mock_storage
        )

    def test_toggle_mode_activates_with_grabber(self):
        mock_grabber = MagicMock()
        self.use_cases.toggle_mode(mock_grabber)
        self.assertTrue(self.state.is_active)
        self.assertTrue(self.state.is_grabbed)
        mock_grabber.grab.assert_called_once()
        self.mock_storage.save_status.assert_called_with("on")

    def test_toggle_mode_deactivates_with_grabber(self):
        self.state.is_active = True
        self.state.is_grabbed = True
        mock_grabber = MagicMock()
        self.use_cases.toggle_mode(mock_grabber)
        self.assertFalse(self.state.is_active)
        self.assertFalse(self.state.is_grabbed)
        mock_grabber.ungrab.assert_called_once()
        self.mock_storage.save_status.assert_called_with("off")

    def test_toggle_mode_debounce(self):
        # First call works
        self.use_cases.toggle_mode()
        self.assertTrue(self.state.is_active)
        
        # Second call immediately after should be ignored (debounce)
        # We don't advance time here
        self.use_cases.toggle_mode()
        self.assertTrue(self.state.is_active) # Still active, didn't toggle back

    def test_next_color_navigation(self):
        self.state.is_active = True
        self.state.color_index = 0
        self.mock_applicator.apply.return_value = True
        
        self.use_cases.next_color()
        self.assertEqual(self.state.color_index, 1)
        self.mock_osd.notify.assert_called()

    def test_prev_color_navigation(self):
        self.state.is_active = True
        self.state.color_index = 1
        self.mock_applicator.apply.return_value = True
        
        self.use_cases.prev_color()
        self.assertEqual(self.state.color_index, 0)
        self.mock_osd.notify.assert_called()

    def test_color_navigation_when_inactive(self):
        self.state.is_active = False
        self.use_cases.next_color()
        self.use_cases.prev_color()
        self.mock_applicator.apply.assert_not_called()

if __name__ == '__main__':
    unittest.main()
