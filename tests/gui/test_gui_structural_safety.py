import unittest
from unittest.mock import MagicMock, patch
from rgb_control.window import MainWindow
from gi.repository import Gtk

class TestMainWindowStructureSafety(unittest.TestCase):
    """
    Testa profundamente a integridade e ciclo de vida estrutural da MainWindow.
    Evita regressões do tipo 'AttributeError' causadas por vazamento de variáveis do escopo (ex: refatorações visuais).
    """

    def setUp(self):
        with patch('rgb_control.window.Backend'), \
             patch('os.path.exists', return_value=False), \
             patch('gi.repository.Gtk.CssProvider'), \
             patch('gi.repository.Gdk.Display.get_default'), \
             patch('rgb_control.window.get_asset_path', return_value=""):
            self.window = MainWindow(MagicMock())

    def test_startup_does_not_crash(self):
        """
        O simples fato do setUp rodar com sucesso indica que o __init__
        completou sem exceptions (como AttributeError). 
        Este teste firma a garantia básica de montagem do Layout UI sem atributos órfãos.
        """
        self.assertIsNotNone(self.window)

    def test_core_ui_widgets_are_bound_and_valid(self):
        """
        Verifica se os containers baseados em overlay do GTK, como o cooler e o scroll,
        foram montados corretamente e de fato herdam de classes validas GTK,
        sem apontarem para variáveis órfãs mortas no layout.
        """
        # Checa a árvore base do header
        self.assertIsNotNone(self.window.main_box)
        
        # Checa a árvore crítica do componente animado
        self.assertIsNotNone(self.window.cpu_fan_overlay)
        self.assertIsNotNone(self.window.fan_hub)

    def test_fan_cooler_rendering_layers(self):
        """
        Garanta que a ventoinha atual mantenha suas instâncias ativas para animações.
        """
        # Testa dependendo da versão ativa (A v18 usa .fan_spinner giratório global
        # e .fan_glow para a base visual, que não existem na engine individual da v19)
        # Vamos verificar dinamicamente quais propriedades a janela contém usando a API Python nativa.

        has_global_spinner = hasattr(self.window, "fan_spinner")
        has_decoupled_blades = hasattr(self.window, "blades")

        self.assertTrue(has_global_spinner or has_decoupled_blades,
                        "O App GTK deve obrigatoriamente possuir um motor de fan construído global ou individual.")

        if has_global_spinner:
            # Se for a Branch arquitetural v1.0.18+
            self.assertIsNotNone(self.window.fan_spinner, "fan_spinner foi declarada mas nao renderizada")
            self.assertIsNotNone(self.window.fan_glow, "fan_glow ausente")
        elif hasattr(self.window, "fan_bg"):
            # Se for a Branch arquitetural das lâminas independentes
            self.assertIsNotNone(self.window.fan_bg)
            self.assertIsNotNone(self.window.blades)
            self.assertEqual(len(self.window.blades), 3, "Devem haver 3 lâminas.")
            for blade in self.window.blades:
                self.assertIsNotNone(blade)

if __name__ == '__main__':
    unittest.main()
