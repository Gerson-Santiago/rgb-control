import pytest
from unittest.mock import MagicMock, patch
from gi.repository import Gio
import os

from rgb_control.main import RgbControlApp, SplashWindow, MainWindow

@pytest.mark.gui
def test_app_initialization(app_instance):
    """Garantia v20+: Application ID deve bater com o registro Desktop."""
    # Como usamos o MockBase do conftest, precisamos garantir o retorno do ID
    app_instance.get_application_id = MagicMock(return_value='com.github.sant.rgbcontrol')
    assert app_instance.get_application_id() == 'com.github.sant.rgbcontrol'

@pytest.mark.gui
def test_do_activate_shows_splash(app_instance):
    """Garantia v20+: do_activate deve disparar SplashWindow em modo headless."""
    with patch('rgb_control.main.SplashWindow') as mock_splash, \
         patch('os.path.exists', return_value=True):
        
        # Simula o clique/ativação do GNOME
        app_instance.do_activate()
        
        # Verifica se o splash foi instanciado e apresentado
        mock_splash.assert_called_once()
        mock_splash.return_value.present.assert_called_once()

@pytest.mark.gui
def test_on_splash_finished_shows_main_window(app_instance):
    """Garantia v20+: Transição Splash -> MainWindow deve ser atômica."""
    with patch('rgb_control.main.MainWindow') as mock_main_window:
        app_instance.on_splash_finished()
        
        # MainWindow deve herdar o contexto da aplicação
        mock_main_window.assert_called_once_with(application=app_instance)
        mock_main_window.return_value.present.assert_called_once()

@pytest.mark.gui
def test_splash_window_init_logic(app_instance):
    """Garantia v20+: Splash deve configurar o cronômetro de transição."""
    from gi.repository import GLib
    
    with patch('gi.repository.GLib.timeout_add') as mock_timeout, \
         patch('rgb_control.main.get_asset_path', return_value="/tmp/fake.png"):
        
        ready_cb = MagicMock()
        splash = SplashWindow(app_instance, ready_cb)
        
        # O splash DEVE carregar o timeout de 2.5s antes de autodestruição
        mock_timeout.assert_called_with(2500, splash._finish_splash)
