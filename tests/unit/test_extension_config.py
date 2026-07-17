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


class TestSSOTContract(unittest.TestCase):
    """
    Testes de contrato que garantem a integridade da Fonte Única de Verdade (SSOT)
    para as cores padrão da extensão GNOME (assets/default_config.json).
    """

    def setUp(self) -> None:
        self.root_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.ssot_path = os.path.join(self.root_dir, "assets", "default_config.json")

    def test_ssot_file_exists_and_is_valid_json(self) -> None:
        """Garante que o arquivo SSOT existe e é um JSON válido."""
        self.assertTrue(
            os.path.exists(self.ssot_path),
            f"Arquivo SSOT ausente: {self.ssot_path}"
        )
        with open(self.ssot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("quick_colors", data)
        self.assertEqual(len(data["quick_colors"]), 3)
        for color in data["quick_colors"]:
            self.assertIn("name", color)
            self.assertIn("hex", color)
            self.assertTrue(color["hex"].startswith("#"), "hex deve começar com #")
            self.assertEqual(len(color["hex"]), 7, "hex deve ter 7 caracteres (#RRGGBB)")

    def test_backend_reads_ssot_file(self) -> None:
        """Garante que o backend lê e retorna exatamente o conteúdo do arquivo SSOT."""
        with open(self.ssot_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

        backend = Backend()
        result = backend.get_default_extension_config()

        self.assertEqual(result, expected,
                         "backend.get_default_extension_config() deve retornar o conteúdo de default_config.json")

    def test_backend_fallback_when_ssot_file_missing(self) -> None:
        """Garante que o backend tem um fallback seguro quando o arquivo SSOT não é encontrado."""
        backend = Backend()
        with patch("os.path.exists", return_value=False):
            result = backend.get_default_extension_config()
        self.assertIn("quick_colors", result)
        self.assertEqual(len(result["quick_colors"]), 3,
                         "Fallback deve sempre ter 3 cores")

    def test_extension_js_fallback_matches_ssot(self) -> None:
        """
        Garante que os valores hardcoded de fallback no extension.js (_loadConfig)
        sejam idênticos aos definidos no arquivo SSOT. Isso evita drift silencioso
        entre a extensão JS e o backend Python.
        """
        extension_js_path = os.path.join(
            self.root_dir, "gnome-extension", "extension.js"
        )
        with open(extension_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        with open(self.ssot_path, "r", encoding="utf-8") as f:
            ssot = json.load(f)

        # Verifica que cada hex e name do SSOT está no código JS
        for color in ssot["quick_colors"]:
            self.assertIn(
                color["hex"],
                js_content,
                f"O hex '{color['hex']}' do SSOT não foi encontrado no extension.js. "
                "Atualize o fallback em _loadConfig() para manter a sincronia."
            )
            self.assertIn(
                color["name"],
                js_content,
                f"O nome '{color['name']}' do SSOT não foi encontrado no extension.js. "
                "Atualize o fallback em _loadConfig() para manter a sincronia."
            )


if __name__ == '__main__':
    unittest.main()

