import sys
import os
import time
import subprocess
import signal
import asyncio
import argparse
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# STUB DE HARDWARE (evdev)
class _EcodeStub:
    EV_KEY         = 1
    KEY_ENTER      = 28
    KEY_RIGHT      = 106
    KEY_LEFT       = 105
    KEY_UP         = 103
    KEY_DOWN       = 108
    KEY_VOLUMEUP   = 115
    KEY_VOLUMEDOWN = 114
    KEY_BACK       = 158

class _EvdevStub(MagicMock):
    ecodes       = _EcodeStub()
    list_devices = MagicMock(return_value=[])

sys.modules["evdev"] = _EvdevStub()

# Importa o daemon da nova localização
from rgb_daemon import main as daemon

@pytest.fixture
def estado():
    return daemon.EstadoDaemon()

@pytest.fixture
def mock_teclado():
    dev = MagicMock()
    dev.name = "XING WEI 2.4G USB USB Composite Device"
    return dev

@pytest.fixture
def mock_subprocess():
    with patch("rgb_daemon.main.subprocess.run") as m:
        m.return_value = MagicMock(returncode=0)
        yield m

class TestEstadoDaemon:
    def test_valores_default(self):
        e = daemon.EstadoDaemon()
        assert e.modo_led_ativo is False
        assert e.indice_cor == 8

class TestPaleta:
    def test_tamanho(self):
        assert len(daemon.PALETA) == 10

class TestMudarCor:
    def test_delta(self, estado):
        with patch("rgb_daemon.main.aplicar_cor", return_value=True), \
             patch("rgb_daemon.main.notificar"):
            estado.indice_cor = 0
            daemon.mudar_cor(estado, +1)
            assert estado.indice_cor == 1

class TestAlternarModo:
    def test_liga(self, estado, mock_teclado):
        with patch("rgb_daemon.main.notificar"):
            daemon.alternar_modo(estado, mock_teclado)
            assert estado.modo_led_ativo is True
            mock_teclado.grab.assert_called_once()

@pytest.mark.asyncio
async def test_listener_teclado_navegacao(estado):
    mock_dev = MagicMock()
    estado.modo_led_ativo = True
    ev_right = MagicMock(type=1, code=106, value=1)
    
    async def mock_loop():
        yield ev_right

    mock_dev.async_read_loop.return_value = mock_loop()
    stop_ev = asyncio.Event()

    with patch("rgb_daemon.main.mudar_cor") as m_mudar:
        task = asyncio.create_task(daemon.listener_teclado(mock_dev, estado, stop_ev))
        await asyncio.sleep(0.1)
        stop_ev.set()
        await task
        assert m_mudar.call_count == 1
