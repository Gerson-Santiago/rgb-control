import sys
import os
import gi
import pytest

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rgb_control.window import MainWindow
from rgb_control.main import SplashWindow

def test_mainwindow_initialization():
    """Garante que a tela principal pode ser instanciada sem exceções e APIs inválidas do GTK4"""
    app = Adw.Application(application_id="com.github.sant.testapp")
    try:
        app.register(None)
    except:
        pass

    try:
        win = MainWindow(application=app)
        assert win is not None
        assert win.get_title() == "RGB Control"
    except Exception as e:
        pytest.fail(f"Falha ao desenhar a interface principal: {e}")

def test_splashwindow_initialization():
    """Garante que a tela de splash Screen instancie corretamente"""
    app = Adw.Application(application_id="com.github.sant.testappsplash")
    try:
        app.register(None)
    except:
        pass
    
    cb_called = []
    def dummy_cb():
        cb_called.append(True)
        
    try:
        win = SplashWindow(application=app, on_ready_callback=dummy_cb)
        assert win is not None
        assert win.get_title() == "Loading RGB Control..."
        
        # O Splash agenda um GLib timeout para se fechar
        win._finish_splash() # Força o fecho manuamente
        assert cb_called[0] is True
    except Exception as e:
        pytest.fail(f"Falha na tela de splash: {e}")
