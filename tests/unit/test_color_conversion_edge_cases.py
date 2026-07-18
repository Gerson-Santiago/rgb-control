# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
from rgb_config.config import hex_to_rgb


class TestColorConversionEdgeCases(unittest.TestCase):
    """
    Testes de robustez para a lógica de conversão HEX → RGB.
    Exploramos limites de input para garantir resiliência total.
    """

    def test_empty_string_returns_black(self) -> None:
        """String vazia deve reverter para preto."""
        self.assertEqual(hex_to_rgb(""), (0, 0, 0))

    def test_none_input_returns_black(self) -> None:
        """Input None deve ser tratado com segurança."""
        self.assertEqual(hex_to_rgb(None), (0, 0, 0))  # type: ignore[arg-type]

    def test_invalid_chars_returns_black(self) -> None:
        """Caracteres não-hexadecimais devem resultar em fallback seguro."""
        self.assertEqual(hex_to_rgb("#ZZZZZZ"), (0, 0, 0))

    def test_short_invalid_hex(self) -> None:
        """HEX de 2 dígitos (inválido) deve resultar em preto."""
        self.assertEqual(hex_to_rgb("#12"), (0, 0, 0))

    def test_four_digit_hex_not_supported(self) -> None:
        """HEX de 4 dígitos não é suportado — deve retornar preto."""
        self.assertEqual(hex_to_rgb("#F00F"), (0, 0, 0))

    def test_whitespace_resilience(self) -> None:
        """Espaços em branco não devem quebrar a conversão de um HEX válido."""
        self.assertEqual(hex_to_rgb("  #FF0000  "), (255, 0, 0))

    def test_valid_hex_lowercase(self) -> None:
        """HEX em minúsculo deve ser tratado corretamente."""
        self.assertEqual(hex_to_rgb("#ff0000"), (255, 0, 0))

    def test_valid_hex_without_hash(self) -> None:
        """HEX sem # deve ser aceito."""
        self.assertEqual(hex_to_rgb("aabbcc"), (170, 187, 204))

    def test_short_form_expansion(self) -> None:
        """Formato curto #F00 deve expandir para (255, 0, 0)."""
        self.assertEqual(hex_to_rgb("#F00"), (255, 0, 0))
        self.assertEqual(hex_to_rgb("#0F0"), (0, 255, 0))
        self.assertEqual(hex_to_rgb("#00F"), (0, 0, 255))


if __name__ == "__main__":
    unittest.main()
