import sys
import pytest
from types import ModuleType
from unittest.mock import MagicMock, patch

def pytest_configure(config):
    """
    Injeta os mocks globais logo na inicialização do Pytest, 
    garantindo que qualquer importe do domain/app/gui acerte os mocks 
    antes de bater na C-Extension verdadeira do Linux.
    """
    # ── 1. Mocks do GTK4 / Libadwaita (Headless) ──
    # O gi.repository agora deve fluir nativamente para suporte a "Headless Real"
    # conforme solicitado no plano Gold Standard.
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, Gio, GLib, Gdk


    # ── 2. Mocks do Evdev (Hardware) ──
    evdev_mock = MagicMock()
    evdev_mock.InputDevice = MagicMock()
    evdev_mock.InputDevice.return_value.name = "Mocked RGB Device"
    sys.modules['evdev'] = evdev_mock


@pytest.fixture(autouse=True)
def mock_subprocess(mocker):
    """
    Mocka globalmente o subprocess.Popen/run para prevenir que 
    os testes alterem os LEDs reais ou tentem acionar notify-send.
    (O 'mocker' vem da biblioteca pytest-mock que instalamos)
    """
    mocker.patch('subprocess.run', return_value=MagicMock(returncode=0))
    mocker.patch('subprocess.Popen')

@pytest.fixture
def fake_filesystem(fs):
    """
    Exposição declarativa do Patcher PyFakeFS para os testes que 
    precisarem manipular /tmp/ ou /dev/input/.
    (A fixture 'fs' vem internamente do pyfakefs)
    """
    yield fs

import uuid
from rgb_control.main import RgbControlApp

@pytest.fixture
def app_instance():
    """
    Fixture Gold Standard para testes de Adw.Application.
    Usa register() p/ mount headless e evita run() bloqueante.
    """
    # Gera ID único para evitar o erro "Objeto já exportado" no DBus do Pytest
    unique_id = f"com.github.sant.rgbcontrol.test_{uuid.uuid4().hex[:8]}"
    
    app = RgbControlApp(application_id=unique_id)
    
    # Garante que get_windows retorne vazio para permitir o flow de do_activate
    app.get_windows = MagicMock(return_value=[])
    
    # O mount 'headless' do Gio.Application
    app.register(None)
    
    yield app


