# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
import os
import json
from unittest.mock import patch, mock_open
from rgb_config.config import (
    get_config_path,
    get_default_config,
    read_config,
    save_config,
)


class TestExtensionConfig(unittest.TestCase):
    def setUp(self) -> None:
        pass  # sem instância de Backend — funções puras

    def test_get_config_path(self) -> None:
        path = get_config_path()
        self.assertTrue(path.endswith("config.json"))
        self.assertIn(".config/rgb-control", path)

    def test_get_default_config(self) -> None:
        default_config = get_default_config()
        self.assertIn("quick_colors", default_config)
        self.assertEqual(len(default_config["quick_colors"]), 8)
        self.assertEqual(default_config["quick_colors"][0]["name"], "Laranja")
        self.assertEqual(default_config["quick_colors"][0]["hex"], "#FF5500")

    @patch("os.path.exists", return_value=False)
    def test_read_config_not_exists_returns_default(self, mock_exists: object) -> None:
        config = read_config()
        self.assertEqual(config, get_default_config())

    @patch("os.path.exists", return_value=True)
    def test_read_config_exists_reads_json(self, mock_exists: object) -> None:
        fake_data = {
            "quick_colors": [
                {"name": "Vermelho", "hex": "#FF0000"},
                {"name": "Verde",    "hex": "#00FF00"},
                {"name": "Azul",     "hex": "#0000FF"},
                {"name": "Laranja",  "hex": "#FF5500"},
                {"name": "Ciano",    "hex": "#00FFFF"},
                {"name": "Roxo",     "hex": "#FF00FF"},
                {"name": "Amarelo",  "hex": "#FFFF00"},
                {"name": "Branco",   "hex": "#FFFFFF"},
            ]
        }
        with patch("builtins.open", mock_open(read_data=json.dumps(fake_data))):
            config = read_config()
            self.assertEqual(config, fake_data)

    @patch("os.path.exists", return_value=True)
    def test_read_config_malformed_returns_default(self, mock_exists: object) -> None:
        with patch("builtins.open", mock_open(read_data="{invalid_json}")):
            config = read_config()
            self.assertEqual(config, get_default_config())

    @patch("os.path.exists", return_value=True)
    def test_read_config_wrong_length_returns_default(self, mock_exists: object) -> None:
        fake_data = {"quick_colors": [{"name": "Vermelho", "hex": "#FF0000"}]}
        with patch("builtins.open", mock_open(read_data=json.dumps(fake_data))):
            config = read_config()
            self.assertEqual(config, get_default_config())

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_config(self, mock_file: object, mock_makedirs: object) -> None:
        fake_data = {
            "quick_colors": [
                {"name": "Vermelho", "hex": "#FF0000"},
                {"name": "Verde",    "hex": "#00FF00"},
                {"name": "Azul",     "hex": "#0000FF"},
                {"name": "Laranja",  "hex": "#FF5500"},
                {"name": "Ciano",    "hex": "#00FFFF"},
                {"name": "Roxo",     "hex": "#FF00FF"},
                {"name": "Amarelo",  "hex": "#FFFF00"},
                {"name": "Branco",   "hex": "#FFFFFF"},
            ]
        }
        save_config(fake_data)
        mock_makedirs.assert_called_once()  # type: ignore[attr-defined]
        mock_file.assert_called_once_with(get_config_path(), "w", encoding="utf-8")  # type: ignore[attr-defined]
        mock_file().write.assert_called()  # type: ignore[attr-defined]


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
            f"Arquivo SSOT ausente: {self.ssot_path}",
        )
        with open(self.ssot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("quick_colors", data)
        self.assertEqual(len(data["quick_colors"]), 8)
        for color in data["quick_colors"]:
            self.assertIn("name", color)
            self.assertIn("hex", color)
            self.assertTrue(color["hex"].startswith("#"), "hex deve começar com #")
            self.assertEqual(len(color["hex"]), 7, "hex deve ter 7 caracteres (#RRGGBB)")

    def test_get_default_config_reads_ssot_file(self) -> None:
        """Garante que get_default_config() retorna exatamente o conteúdo do SSOT."""
        with open(self.ssot_path, "r", encoding="utf-8") as f:
            expected = json.load(f)
        result = get_default_config()
        self.assertEqual(result, expected)

    def test_fallback_when_ssot_file_missing(self) -> None:
        """Garante que há fallback seguro quando o SSOT não é encontrado."""
        with patch("os.path.exists", return_value=False):
            result = get_default_config()
        self.assertIn("quick_colors", result)
        self.assertEqual(len(result["quick_colors"]), 8,
                         "Fallback deve sempre ter 8 cores")

    def test_extension_js_fallback_matches_ssot(self) -> None:
        """
        Garante que os valores hardcoded de fallback no extension.js (_loadConfig)
        sejam idênticos aos definidos no arquivo SSOT — evita drift silencioso.
        """
        extension_js_path = os.path.join(
            self.root_dir, "gnome-extension", "extension.js"
        )
        with open(extension_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        with open(self.ssot_path, "r", encoding="utf-8") as f:
            ssot = json.load(f)

        for color in ssot["quick_colors"]:
            self.assertIn(
                color["hex"],
                js_content,
                f"O hex '{color['hex']}' do SSOT não foi encontrado no extension.js. "
                "Atualize o fallback em _loadConfig() para manter a sincronia.",
            )
            self.assertIn(
                color["name"],
                js_content,
                f"O nome '{color['name']}' do SSOT não foi encontrado no extension.js. "
                "Atualize o fallback em _loadConfig() para manter a sincronia.",
            )


if __name__ == "__main__":
    unittest.main()
