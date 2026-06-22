import unittest
import os
import json
from unittest.mock import patch, mock_open
from rgb_control.backend import Backend

class TestExtensionConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = Backend()

    def test_get_extension_config_path(self) -> None:
        path = self.backend.get_extension_config_path()
        self.assertTrue(path.endswith("config.json"))
        self.assertIn(".config/rgb-control", path)

    def test_get_default_extension_config(self) -> None:
        default_config = self.backend.get_default_extension_config()
        self.assertIn("quick_colors", default_config)
        self.assertEqual(len(default_config["quick_colors"]), 3)
        self.assertEqual(default_config["quick_colors"][0]["name"], "Laranja")
        self.assertEqual(default_config["quick_colors"][0]["hex"], "#FF5500")

    @patch("os.path.exists", return_value=False)
    def test_get_extension_config_not_exists_returns_default(self, mock_exists) -> None:
        config = self.backend.get_extension_config()
        self.assertEqual(config, self.backend.get_default_extension_config())

    @patch("os.path.exists", return_value=True)
    def test_get_extension_config_exists_reads_json(self, mock_exists) -> None:
        fake_data = {
            "quick_colors": [
                {"name": "Vermelho", "hex": "#FF0000"},
                {"name": "Verde", "hex": "#00FF00"},
                {"name": "Azul", "hex": "#0000FF"}
            ]
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(fake_data))):
            config = self.backend.get_extension_config()
            self.assertEqual(config, fake_data)

    @patch("os.path.exists", return_value=True)
    def test_get_extension_config_malformed_returns_default(self, mock_exists) -> None:
        # JSON inválido
        with patch("builtins.open", mock_open(read_data="{invalid_json}")):
            config = self.backend.get_extension_config()
            self.assertEqual(config, self.backend.get_default_extension_config())

    @patch("os.path.exists", return_value=True)
    def test_get_extension_config_wrong_length_returns_default(self, mock_exists) -> None:
        # JSON válido mas com quantidade errada de cores
        fake_data = {
            "quick_colors": [
                {"name": "Vermelho", "hex": "#FF0000"}
            ]
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(fake_data))):
            config = self.backend.get_extension_config()
            self.assertEqual(config, self.backend.get_default_extension_config())

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_extension_config(self, mock_file, mock_makedirs) -> None:
        fake_data = {
            "quick_colors": [
                {"name": "Vermelho", "hex": "#FF0000"},
                {"name": "Verde", "hex": "#00FF00"},
                {"name": "Azul", "hex": "#0000FF"}
            ]
        }
        
        self.backend.save_extension_config(fake_data)
        
        # Verifica se tentou criar a pasta ~/.config/rgb-control
        mock_makedirs.assert_called_once()
        # Verifica se tentou escrever o JSON no arquivo
        mock_file.assert_called_once_with(self.backend.get_extension_config_path(), "w", encoding="utf-8")
        mock_file().write.assert_called()

if __name__ == '__main__':
    unittest.main()
