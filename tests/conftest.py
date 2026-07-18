import sys
import pytest
from unittest.mock import MagicMock


def pytest_configure(config: pytest.Config) -> None:
    """
    Injeta mocks globais na inicialização do Pytest.
    Com a remoção do app GTK4, os únicos mocks necessários são
    os do subprocess (para não acionar LEDs reais durante testes).
    """
    # Mock do evdev (hardware) — mantido para compatibilidade futura
    evdev_mock = MagicMock()
    evdev_mock.InputDevice = MagicMock()
    evdev_mock.InputDevice.return_value.name = "Mocked RGB Device"
    sys.modules["evdev"] = evdev_mock


@pytest.fixture(autouse=True)
def mock_subprocess(mocker: pytest.MonkeyPatch) -> None:
    """
    Mocka globalmente subprocess.Popen/run para prevenir que
    os testes alterem os LEDs reais durante a execução.
    """
    mocker.patch("subprocess.run", return_value=MagicMock(returncode=0))  # type: ignore[attr-defined]
    mocker.patch("subprocess.Popen")  # type: ignore[attr-defined]


@pytest.fixture
def fake_filesystem(fs: object) -> object:  # type: ignore[misc]
    """
    Exposição declarativa do PyFakeFS para testes que precisam
    manipular o filesystem de forma isolada.
    """
    yield fs  # type: ignore[misc]
