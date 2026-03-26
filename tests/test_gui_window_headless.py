import unittest
from unittest.mock import MagicMock, patch

# Mocking Gi (GObject Introspection) BEFORE importing window
import sys
from types import ModuleType

# Create a robust mock for gi
gi_mock = MagicMock()
gi_mock.require_version = MagicMock()
sys.modules['gi'] = gi_mock

gi_repository = ModuleType('gi.repository')
sys.modules['gi.repository'] = gi_repository

def mock_repo(name):
    m = MagicMock()
    setattr(gi_repository, name, m)
    sys.modules[f'gi.repository.{name}'] = m
    return m

Gtk = mock_repo('Gtk')
Adw = mock_repo('Adw')
GLib = mock_repo('GLib')
Gio = mock_repo('Gio')
Gdk = mock_repo('Gdk')

# Mock inheritance for MainWindow
class MockAppWindow: 
    def __init__(self, *args, **kwargs): pass
    def set_title(self, *args): pass
    def set_default_size(self, *args): pass
    def set_content(self, *args): pass
    def add_css_class(self, *args): pass
    def set_halign(self, *args): pass
    def append(self, *args): pass
    def set_margin_top(self, *args): pass
    def set_margin_bottom(self, *args): pass
    def set_margin_start(self, *args): pass
    def set_margin_end(self, *args): pass

Adw.ApplicationWindow = MockAppWindow

from rgb_control.window import MainWindow

class TestGuiWindowHeadless(unittest.TestCase):
    def setUp(self):
        # Mocking the Backend
        self.patcher_backend = patch('rgb_control.window.Backend')
        self.mock_backend_class = self.patcher_backend.start()
        self.mock_backend = self.mock_backend_class.return_value
        
        # Mocking Gtk.Application
        self.mock_app = MagicMock()
        
        # Instantiate MainWindow
        with patch('gi.repository.Gtk.Picture.new_for_filename'), \
             patch('gi.repository.Gtk.CssProvider'), \
             patch('gi.repository.Gdk.Display.get_default'), \
             patch('rgb_control.window.get_asset_path', return_value="/tmp/logo.svg"), \
             patch('os.path.exists', return_value=True):
            self.window = MainWindow(self.mock_app)
            
            # Mock the switches that were created in __init__
            self.window.switch_svc = MagicMock()
            self.window.switch_mode = MagicMock()

    def tearDown(self):
        self.patcher_backend.stop()

    def test_on_service_notify(self):
        mock_row = MagicMock()
        mock_row.get_active.return_value = True
        self.window.on_service_notify(mock_row, None)
        self.mock_backend.set_service_state.assert_called_with(True)

    def test_on_mode_notify(self):
        mock_row = MagicMock()
        mock_row.get_active.return_value = True
        self.window.on_mode_notify(mock_row, None)
        self.mock_backend.set_led_mode.assert_called_with(True)

    def test_on_color_clicked(self):
        self.window.on_color_clicked(MagicMock(), "#FF0000", "Vermelho")
        self.mock_backend.apply_color.assert_called_with("#FF0000", "Vermelho")

if __name__ == '__main__':
    unittest.main()
