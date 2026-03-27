import unittest
from rgb_daemon.domain import DaemonState, PALETTE, Color

class TestDaemonDomain(unittest.TestCase):
    def test_initial_state(self):
        state = DaemonState()
        self.assertFalse(state.is_active)
        self.assertEqual(state.color_index, 8)
        self.assertEqual(state.get_current_color().name, "Branco")

    def test_invalid_hex_raises_error(self):
        with self.assertRaisesRegex(ValueError, "deve ter 6 caracteres"):
            Color("Curta", "FF")
        with self.assertRaisesRegex(ValueError, "não alfanumérico hex"):
            Color("Lixo", "ZZZZZZ")

    def test_next_color_cycling(self):
        state = DaemonState(color_index=len(PALETTE) - 1)
        color = state.next_color()
        self.assertEqual(color.name, "Vermelho")
        self.assertEqual(state.color_index, 0)

    def test_prev_color_cycling(self):
        state = DaemonState(color_index=0)
        color = state.prev_color()
        self.assertEqual(color.name, "Desligar")
        self.assertEqual(state.color_index, len(PALETTE) - 1)

if __name__ == '__main__':
    unittest.main()
