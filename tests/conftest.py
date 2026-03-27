import sys
import pytest
from types import ModuleType
from unittest.mock import MagicMock

def pytest_configure(config):
    """
    Injeta os mocks globais logo na inicialização do Pytest, 
    garantindo que qualquer importe do domain/app/gui acerte os mocks 
    antes de bater na C-Extension verdadeira do Linux.
    """
    # ── 1. Mocks do GTK4 / Libadwaita (Headless) ──
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
    _mock_repo('GLib')
    _mock_repo('Gio')
    _mock_repo('Gdk')

    class _MockBase:
        def __init__(self, *a, **kw): pass
        def __getattr__(self, name): return MagicMock()

    Adw.ApplicationWindow = _MockBase
    Adw.Application       = _MockBase
    Gtk.Window            = _MockBase

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
