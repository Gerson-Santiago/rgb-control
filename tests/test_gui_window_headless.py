import unittest
from unittest.mock import MagicMock, patch

# Mocking Gi (GObject Introspection) before importing window
import sys
mock_gi = MagicMock()
sys.modules['gi'] = mock_gi
sys.modules['gi.repository'] = MagicMock()
sys.modules['gi.repository.Gtk'] = MagicMock()
sys.modules['gi.repository.Adw'] = MagicMock()
sys.modules['gi.repository.GLib'] = MagicMock()

from rgb_control.window import MainWindow

class TestGuiWindowHeadless(unittest.TestCase):
    def setUp(self):
        # Mocking the Backend used in MainWindow
        self.patcher_backend = patch('rgb_control.window.Backend')
        self.mock_backend_class = self.patcher_backend.start()
        self.mock_backend = self.mock_backend_class.return_value
        
        # Mocking Gtk.Application
        self.mock_app = MagicMock()
        
        # We need to mock the UI objects that MainWindow expects to find (Builder)
        with patch('gi.repository.Gtk.Builder') as mock_builder:
            self.window = MainWindow(self.mock_app)
            # Simula que o builder encontrou os objetos
            self.window.switch_servico = MagicMock()
            self.window.switch_modo = MagicMock()
            self.window.main_stack = MagicMock()

    def tearDown(self):
        self.patcher_backend.stop()

    def test_on_toggle_servico_active(self):
        # Simula o clique no switch de serviço para ativar
        self.window.switch_servico.get_active.return_value = True
        self.window.on_toggle_servico(self.window.switch_servico)
        
        self.mock_backend.set_service_state.assert_called_with(True)

    def test_on_toggle_modo_active(self):
        # Simula o clique no botão de modo LED para ativar
        self.window.switch_modo.get_active.return_value = True
        self.window.on_toggle_modo(self.window.switch_modo)
        
        self.mock_backend.set_led_mode.assert_called_with(True)

    def test_on_color_clicked(self):
        # Simula o clique em um botão de cor
        mock_btn = MagicMock()
        mock_btn.get_name.return_value = "Vermelho"
        # Precisamos de um valor hexadecimal fictício ou mockado
        # MainWindow busca a cor na PALETA
        self.window.on_color_clicked(mock_btn)
        
        # Verifica se o backend foi chamado para aplicar a cor
        self.mock_backend.apply_color.assert_called()

if __name__ == '__main__':
    unittest.main()
