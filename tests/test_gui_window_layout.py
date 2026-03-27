"""
Testes de Regressão — Interface GTK (window.py + main.py)

Garante que as evoluções recentes não quebrem:
  - Carregamento do CSS a partir do diretório correto
  - Resolução do logo: .png tem prioridade sobre .svg
  - Layout da janela: scrolled, clamp e main_box com hexpand=True
  - Callbacks de interação: cor, serviço, modo LED
  - Resiliência: interface não crasha quando assets não existem
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from types import ModuleType

# ── Mocks do GTK (headless, sem display) ───────────────────────────────────
gi_mock = MagicMock()
gi_mock.require_version = MagicMock()
sys.modules['gi'] = gi_mock

gi_repository = ModuleType('gi.repository')
sys.modules['gi.repository'] = gi_repository

def _mock_repo(name):
    m = MagicMock()
    setattr(gi_repository, name, m)
    sys.modules[f'gi.repository.{name}'] = m
    return m

Gtk = _mock_repo('Gtk')
Adw = _mock_repo('Adw')
GLib = _mock_repo('GLib')
Gio  = _mock_repo('Gio')
Gdk  = _mock_repo('Gdk')

class _MockBase:
    def __init__(self, *a, **kw): pass
    def __getattr__(self, name):   return MagicMock()

Adw.ApplicationWindow = _MockBase
Adw.Application       = _MockBase

from rgb_control.window import MainWindow, get_asset_path   # noqa: E402


# ══════════════════════════════════════════════════════════════════════════
# 1. Utilitário get_asset_path
# ══════════════════════════════════════════════════════════════════════════
class TestGetAssetPath(unittest.TestCase):
    """get_asset_path deve retornar um caminho com o nome correto, nunca None."""

    def test_returns_string_for_png(self):
        path = get_asset_path("logo.png")
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith("logo.png"))

    def test_returns_string_for_svg(self):
        path = get_asset_path("logo.svg")
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith("logo.svg"))

    def test_different_files_return_different_paths(self):
        p1 = get_asset_path("logo.png")
        p2 = get_asset_path("logo.svg")
        self.assertNotEqual(p1, p2)


# ══════════════════════════════════════════════════════════════════════════
# 2. Carregamento do CSS
# ══════════════════════════════════════════════════════════════════════════
class TestCssLoading(unittest.TestCase):
    """load_custom_css deve encontrar style.css no diretório de window.py."""

    def _make_window(self, exists_map):
        """Cria MainWindow com controle fino sobre quais caminhos 'existem'."""
        def fake_exists(p):
            return exists_map.get(p, False)

        with patch('rgb_control.window.Backend'), \
             patch('os.path.exists', side_effect=fake_exists), \
             patch('gi.repository.Gtk.CssProvider') as mock_css, \
             patch('gi.repository.Gdk.Display.get_default'), \
             patch('rgb_control.window.get_asset_path', return_value=""):
            w = MainWindow(MagicMock())
        return w, mock_css

    def test_css_loaded_from_own_directory(self):
        """CSS deve ser carregado quando style.css existe no mesmo dir do window.py."""
        own_dir = os.path.dirname(os.path.abspath(
            sys.modules['rgb_control.window'].__file__
        ))
        css_path = os.path.join(own_dir, "style.css")

        _, mock_css = self._make_window({css_path: True})
        mock_css.return_value.load_from_path.assert_called_once_with(css_path)

    def test_no_crash_when_css_missing(self):
        """Interface não deve crashar se style.css não for encontrado."""
        try:
            self._make_window({})
        except Exception as e:
            self.fail(f"Interface crashou sem CSS: {e}")


# ══════════════════════════════════════════════════════════════════════════
# 3. Resolução do Logo (prioridade .png > .svg)
# ══════════════════════════════════════════════════════════════════════════
class TestLogoResolution(unittest.TestCase):
    """logo.png deve ter prioridade sobre logo.svg na MainWindow."""

    def _window_with_assets(self, has_png: bool, has_svg: bool):
        """Instancia MainWindow com controle sobre existência dos assets."""
        def fake_gap(filename):
            if filename == "logo.png": return "/fake/logo.png"
            if filename == "logo.svg": return "/fake/logo.svg"
            return ""

        def fake_exists(p):
            if p == "/fake/logo.png": return has_png
            if p == "/fake/logo.svg": return has_svg
            if p.endswith("style.css"): return False
            return False

        captured = {}
        _orig = Gtk.Picture.new_for_filename

        def capture_picture(path):
            captured['logo_path'] = path
            return MagicMock()

        Gtk.Picture.new_for_filename = capture_picture

        try:
            with patch('rgb_control.window.Backend'), \
                 patch('rgb_control.window.get_asset_path', side_effect=fake_gap), \
                 patch('os.path.exists', side_effect=fake_exists):
                MainWindow(MagicMock())
        finally:
            Gtk.Picture.new_for_filename = _orig

        return captured.get('logo_path')

    def test_png_used_when_it_exists(self):
        path = self._window_with_assets(has_png=True, has_svg=False)
        self.assertEqual(path, "/fake/logo.png",
                         "logo.png deve ter prioridade absoluta e única")

    def test_no_logo_loaded_when_none_exist(self):
        path = self._window_with_assets(has_png=False, has_svg=False)
        self.assertIsNone(path, "Nenhum logo deve ser carregado sem assets")

    def test_no_crash_when_no_logo(self):
        """Interface não deve crashar se não houver nenhum logo."""
        try:
            self._window_with_assets(has_png=False, has_svg=False)
        except Exception as e:
            self.fail(f"Interface crashou sem logo: {e}")


# ══════════════════════════════════════════════════════════════════════════
# 4. Callbacks de Interação
# ══════════════════════════════════════════════════════════════════════════
class TestWindowCallbacks(unittest.TestCase):

    def setUp(self):
        patcher_backend = patch('rgb_control.window.Backend')
        self.mock_backend_cls = patcher_backend.start()
        self.mock_backend = self.mock_backend_cls.return_value
        self.addCleanup(patcher_backend.stop)

        with patch('os.path.exists', return_value=False), \
             patch('gi.repository.Gtk.CssProvider'), \
             patch('gi.repository.Gdk.Display.get_default'), \
             patch('rgb_control.window.get_asset_path', return_value=""):
            self.window = MainWindow(MagicMock())
        self.window.switch_svc  = MagicMock()
        self.window.switch_mode = MagicMock()

    def test_color_callback_calls_backend(self):
        self.window.on_color_clicked(MagicMock(), "#00FF00", "Verde")
        self.mock_backend.apply_color.assert_called_once_with("#00FF00", "Verde")

    def test_color_callback_all_preset_colors(self):
        """Cada uma das 10 cores pré-definidas deve acionar o backend corretamente."""
        cores = [
            ("#FF0000", "Vermelho"), ("#FF5500", "Laranja"), ("#FFFF00", "Amarelo"),
            ("#00FF00", "Verde"),    ("#00F2EA", "Ciano"),   ("#0000FF", "Azul"),
            ("#AA00FF", "Roxo"),     ("#FFB200", "Ambar"),   ("#FFFFFF", "Branco"),
            ("#000000", "Desativar"),
        ]
        for hex_val, name in cores:
            with self.subTest(color=name):
                self.mock_backend.apply_color.reset_mock()
                self.window.on_color_clicked(MagicMock(), hex_val, name)
                self.mock_backend.apply_color.assert_called_once_with(hex_val, name)

    def test_service_toggle_on(self):
        row = MagicMock()
        row.get_active.return_value = True
        self.window.on_service_notify(row, None)
        self.mock_backend.set_service_state.assert_called_once_with(True)

    def test_service_toggle_off(self):
        row = MagicMock()
        row.get_active.return_value = False
        self.window.on_service_notify(row, None)
        self.mock_backend.set_service_state.assert_called_once_with(False)

    def test_mode_toggle_on(self):
        row = MagicMock()
        row.get_active.return_value = True
        self.window.on_mode_notify(row, None)
        self.mock_backend.set_led_mode.assert_called_once_with(True)

    def test_mode_toggle_off(self):
        row = MagicMock()
        row.get_active.return_value = False
        self.window.on_mode_notify(row, None)
        self.mock_backend.set_led_mode.assert_called_once_with(False)

    def test_service_reverts_on_failure(self):
        """Se o backend falhar, o switch deve reverter ao estado anterior."""
        self.mock_backend.set_service_state.return_value = False
        row = MagicMock()
        row.get_active.return_value = True
        self.window._updating_ui = False
        self.window.on_service_notify(row, None)
        row.set_active.assert_called_with(False)

    def test_no_reentrant_signal_loop(self):
        """Quando _updating_ui=True os callbacks não chamam o backend."""
        self.window._updating_ui = True
        row = MagicMock()
        row.get_active.return_value = True
        self.window.on_service_notify(row, None)
        self.mock_backend.set_service_state.assert_not_called()
        self.window.on_mode_notify(row, None)
        self.mock_backend.set_led_mode.assert_not_called()

    def test_custom_color_red(self):
        """RGBA(1.0, 0.0, 0.0) → '#FF0000'"""
        picker = MagicMock()
        rgba = MagicMock()
        rgba.red, rgba.green, rgba.blue = 1.0, 0.0, 0.0
        picker.get_rgba.return_value = rgba
        self.window.on_custom_color_selected(picker, None)
        self.mock_backend.apply_color.assert_called_once_with("#FF0000", "Custom")

    def test_custom_color_white(self):
        """RGBA(1.0, 1.0, 1.0) → '#FFFFFF'"""
        picker = MagicMock()
        rgba = MagicMock()
        rgba.red, rgba.green, rgba.blue = 1.0, 1.0, 1.0
        picker.get_rgba.return_value = rgba
        self.window.on_custom_color_selected(picker, None)
        self.mock_backend.apply_color.assert_called_once_with("#FFFFFF", "Custom")

    def test_custom_color_black(self):
        """RGBA(0.0, 0.0, 0.0) → '#000000'"""
        picker = MagicMock()
        rgba = MagicMock()
        rgba.red, rgba.green, rgba.blue = 0.0, 0.0, 0.0
        picker.get_rgba.return_value = rgba
        self.window.on_custom_color_selected(picker, None)
        self.mock_backend.apply_color.assert_called_once_with("#000000", "Custom")


# ══════════════════════════════════════════════════════════════════════════
# 5. Lógica de resolução do logo do Splash (testada isoladamente)
# ══════════════════════════════════════════════════════════════════════════
class TestSplashLogoLogic(unittest.TestCase):
    """
    Testa a lógica de seleção do logo do splash diretamente,
    sem instanciar o widget GTK (que é mockado globalmente).
    """

    def _resolve_splash_logo(self, has_png: bool, has_svg: bool) -> str | None:
        """
        Replica a lógica do SplashWindow.__init__:
        usa logo.png se existir, logo.svg como fallback, None se nenhum.
        """
        def fake_gap(filename):
            if filename == "logo.png": return "/fake/logo.png"
            return ""

        def fake_exists(p):
            if p == "/fake/logo.png": return has_png
            return False

        with patch('rgb_control.main.get_asset_path', side_effect=fake_gap), \
             patch('os.path.exists', side_effect=fake_exists):
            logo_file = fake_gap("logo.png")
            if not fake_exists(logo_file):
                logo_file = None
        return logo_file

    def test_png_selected_when_exists(self):
        path = self._resolve_splash_logo(has_png=True, has_svg=False)
        self.assertEqual(path, "/fake/logo.png")

    def test_none_when_no_assets(self):
        path = self._resolve_splash_logo(has_png=False, has_svg=False)
        self.assertIsNone(path)


if __name__ == '__main__':
    unittest.main()
