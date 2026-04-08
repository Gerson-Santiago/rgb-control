import unittest
from rgb_control.utils import hex_to_rgba_tuple

class TestColorConversionEdgeCases(unittest.TestCase):
    """
    Testes de robustez para a lógica de conversão HEX -> RGBA.
    Seguindo a política 'Test First', exploramos limites de input.
    """

    def test_empty_string_returns_black(self):
        """String vazia deve reverter para preto opaco."""
        self.assertEqual(hex_to_rgba_tuple(""), (0, 0, 0, 1.0))

    def test_none_input_returns_black(self):
        """Input None deve ser tratado com segurança."""
        # Note: if the type hint is str, this tests resilience against runtime type errors
        self.assertEqual(hex_to_rgba_tuple(None), (0, 0, 0, 1.0)) # type: ignore

    def test_invalid_chars_returns_black(self):
        """Caracteres não-hexadecimais devem ser ignorados ou resultar em falha segura."""
        self.assertEqual(hex_to_rgba_tuple("#ZZZZZZ"), (0, 0, 0, 1.0))

    def test_short_invalid_hex(self):
        """HEX de 2 dígitos (inválido) deve resultar em preto."""
        self.assertEqual(hex_to_rgba_tuple("#12"), (0, 0, 0, 1.0))

    def test_four_digit_hex_with_alpha_not_supported(self):
        """HEX de 4 dígitos não é suportado oficialmente, deve retornar preto."""
        self.assertEqual(hex_to_rgba_tuple("#F00F"), (0, 0, 0, 1.0))

    def test_whitespace_resilience(self):
        """Espaços em branco não devem quebrar a conversão se houver um HEX válido."""
        self.assertEqual(hex_to_rgba_tuple("  #FF0000  "), (255, 0, 0, 1.0))

if __name__ == '__main__':
    unittest.main()
