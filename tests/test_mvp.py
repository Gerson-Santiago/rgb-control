
"""
tests/test_mvp.py — Suite pytest para mvp.py v2
================================================
Estratégia híbrida:
  • Funções de lógica pura  → testadas com mocks (sem hardware)
  • Erros de hardware       → simulados com side_effect
  • Fixtures                → resetam EstadoDaemon entre testes
  • Parametrize             → múltiplos valores sem duplicar código

Rodar:
    python3 -m pytest tests/ -v
    python3 -m pytest tests/ -v --cov=mvp --cov-report=term-missing
"""

import sys
import time
import subprocess
import signal
import asyncio
from unittest.mock import MagicMock, patch, call

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# STUB DE HARDWARE (registrado ANTES do import do módulo)
# ─────────────────────────────────────────────────────────────────────────────

class _EcodeStub:
    """Códigos reais do kernel Linux — confirmados nos logs evtest."""
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


_evdev_stub = _EvdevStub()
sys.modules["evdev"] = _evdev_stub

import mvp  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def estado() -> mvp.EstadoDaemon:
    """Estado limpo para cada teste."""
    return mvp.EstadoDaemon()


@pytest.fixture
def mock_teclado() -> MagicMock:
    """Device de teclado mockado."""
    dev = MagicMock()
    dev.name = "XING WEI 2.4G USB USB Composite Device"
    return dev


@pytest.fixture
def mock_subprocess():
    with patch("mvp.subprocess.run") as m:
        m.return_value = MagicMock(returncode=0)
        yield m


@pytest.fixture
def mock_notificar():
    with patch("mvp.notificar") as m:
        yield m


@pytest.fixture
def mock_aplicar_ok():
    with patch("mvp.aplicar_cor", return_value=True) as m:
        yield m


# ─────────────────────────────────────────────────────────────────────────────
# 1. EstadoDaemon — dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestEstadoDaemon:

    def test_valores_default(self):
        e = mvp.EstadoDaemon()
        assert e.modo_led_ativo is False
        assert e.indice_cor     == 8
        assert e.ok_press_time  is None
        assert e.grabbed        is False

    def test_mutavel(self):
        e = mvp.EstadoDaemon()
        e.modo_led_ativo = True
        e.indice_cor = 3
        assert e.modo_led_ativo is True
        assert e.indice_cor == 3

    def test_instancias_independentes(self):
        e1 = mvp.EstadoDaemon()
        e2 = mvp.EstadoDaemon()
        e1.modo_led_ativo = True
        assert e2.modo_led_ativo is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Paleta
# ─────────────────────────────────────────────────────────────────────────────

class TestPaleta:

    def test_tamanho(self):
        assert len(mvp.PALETA) == 10

    @pytest.mark.parametrize("idx,nome,hex_esperado", [
        (0, "Vermelho", "FF0000"),
        (3, "Verde",    "00FF00"),
        (8, "Branco",   "FFFFFF"),
        (9, "Desligar", "000000"),
    ])
    def test_cores_especificas(self, idx, nome, hex_esperado):
        n, h = mvp.PALETA[idx]
        assert n == nome
        assert h == hex_esperado

    @pytest.mark.parametrize("nome,cor", mvp.PALETA)
    def test_hex_valido(self, nome, cor):
        import re
        assert re.fullmatch(r"[0-9A-Fa-f]{6}", cor), f"{nome}: '{cor}' inválido"


# ─────────────────────────────────────────────────────────────────────────────
# 3. mudar_cor
# ─────────────────────────────────────────────────────────────────────────────

class TestMudarCor:

    @pytest.mark.parametrize("inicio,delta,esperado", [
        (0, +1, 1),
        (3, +1, 4),
        (3, -1, 2),
    ])
    def test_delta(self, inicio, delta, esperado, estado, mock_notificar, mock_aplicar_ok):
        estado.indice_cor = inicio
        mvp.mudar_cor(estado, delta)
        assert estado.indice_cor == esperado

    def test_ciclico_frente(self, estado, mock_notificar, mock_aplicar_ok):
        estado.indice_cor = len(mvp.PALETA) - 1
        mvp.mudar_cor(estado, +1)
        assert estado.indice_cor == 0

    def test_ciclico_tras(self, estado, mock_notificar, mock_aplicar_ok):
        estado.indice_cor = 0
        mvp.mudar_cor(estado, -1)
        assert estado.indice_cor == len(mvp.PALETA) - 1

    def test_sem_notificacao_se_falha(self, estado, mock_notificar):
        with patch("mvp.aplicar_cor", return_value=False):
            mvp.mudar_cor(estado, +1)
        mock_notificar.assert_not_called()

    def test_aplica_hex_correto(self, estado, mock_notificar):
        estado.indice_cor = 0   # Vermelho
        with patch("mvp.aplicar_cor", return_value=True) as m:
            mvp.mudar_cor(estado, +1)   # → Laranja (idx=1)
        m.assert_called_once_with(mvp.PALETA[1][1], mvp.PALETA[1][0])


# ─────────────────────────────────────────────────────────────────────────────
# 4. alternar_modo — com grab/ungrab
# ─────────────────────────────────────────────────────────────────────────────

class TestAlternarModo:

    def test_liga(self, estado, mock_teclado, mock_notificar):
        mvp.alternar_modo(estado, mock_teclado)
        assert estado.modo_led_ativo is True
        assert estado.grabbed is True
        mock_teclado.grab.assert_called_once()

    def test_desliga(self, estado, mock_teclado, mock_notificar):
        estado.modo_led_ativo = True
        estado.grabbed        = True
        mvp.alternar_modo(estado, mock_teclado)
        assert estado.modo_led_ativo is False
        assert estado.grabbed is False
        mock_teclado.ungrab.assert_called_once()

    def test_toggle_duplo(self, estado, mock_teclado, mock_notificar):
        mvp.alternar_modo(estado, mock_teclado)
        mvp.alternar_modo(estado, mock_teclado)
        assert estado.modo_led_ativo is False

    def test_grab_falha_silenciosa(self, estado, mock_notificar):
        """grab() com OSError não deve derrubar o daemon."""
        dev = MagicMock()
        dev.grab.side_effect = OSError("device busy")
        try:
            mvp.alternar_modo(estado, dev)
        except OSError:
            pytest.fail("alternar_modo() propagou OSError")
        assert estado.grabbed is False  # não marcou como grabbed

    def test_sem_device_nao_crasha(self, estado, mock_notificar):
        """dev_teclado=None é suportado (device não encontrado)."""
        mvp.alternar_modo(estado, None)
        assert estado.modo_led_ativo is True

    def test_notifica_ao_ligar(self, estado, mock_teclado, mock_notificar):
        mvp.alternar_modo(estado, mock_teclado)
        titulo, corpo = mock_notificar.call_args[0][:2]
        assert "ATIVO" in corpo

    def test_notifica_ao_desligar(self, estado, mock_teclado, mock_notificar):
        estado.modo_led_ativo = True
        mvp.alternar_modo(estado, mock_teclado)
        titulo, corpo = mock_notificar.call_args[0][:2]
        assert "Desativado" in corpo


# ─────────────────────────────────────────────────────────────────────────────
# 5. Long Press — lógica de tempo
# ─────────────────────────────────────────────────────────────────────────────

class TestLongPress:

    @pytest.mark.parametrize("duracao_s,deve_alternar", [
        (3.1, True),
        (5.0, True),
        (0.5, False),
        (2.9, False),
    ])
    def test_limiar(self, duracao_s, deve_alternar, estado, mock_notificar, mock_teclado):
        with patch("mvp.alternar_modo") as mock_alt:
            t0 = time.time() - duracao_s
            estado.ok_press_time = t0
            duracao = time.time() - estado.ok_press_time
            estado.ok_press_time = None
            if duracao >= mvp.LONG_PRESS_TIME:
                mvp.alternar_modo(estado, mock_teclado)

            if deve_alternar:
                mock_alt.assert_called_once()
            else:
                mock_alt.assert_not_called()

    def test_long_press_time_ergonomico(self):
        assert 2.0 <= mvp.LONG_PRESS_TIME <= 5.0


# ─────────────────────────────────────────────────────────────────────────────
# 6. aplicar_cor
# ─────────────────────────────────────────────────────────────────────────────

class TestAplicarCor:

    def test_sucesso_com_usuario_sant(self, mock_subprocess):
        """v2.4: Aplica via sudo -u sant bash rbg.sh."""
        assert mvp.aplicar_cor("FF0000", "Vermelho") is True
        cmd = mock_subprocess.call_args_list[0][0][0]
        assert "sudo" in cmd
        assert "-u" in cmd
        assert "sant" in cmd
        assert "rbg.sh" in cmd[4]
        assert "vermelho" in cmd[5]

    def test_fallback_sudo(self, mock_subprocess):
        mock_subprocess.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]
        assert mvp.aplicar_cor("00FF00", "Verde") is True
        assert mock_subprocess.call_count == 2

    def test_ambas_falham(self, mock_subprocess):
        mock_subprocess.side_effect = [MagicMock(returncode=1), MagicMock(returncode=1)]
        assert mvp.aplicar_cor("0000FF", "Azul") is False

    def test_timeout(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired("openrgb", 5)
        assert mvp.aplicar_cor("FFFFFF", "Branco") is False

    @pytest.mark.parametrize("entrada,nome,esperado", [
        ("FF0000", "Vermelho", "vermelho"),
        ("#FF0000", "Laranja",  "laranja"),
    ])
    def test_passa_nome_correto_ao_script(self, entrada, nome, esperado, mock_subprocess):
        mvp.aplicar_cor(entrada, nome)
        cmd = mock_subprocess.call_args_list[0][0][0]
        # v2.4: o script recebe o nome da cor como último argumento
        assert cmd[-1] == esperado


# ─────────────────────────────────────────────────────────────────────────────
# 7. notificar
# ─────────────────────────────────────────────────────────────────────────────

class TestNotificar:

    def test_chama_notify_send(self, mock_subprocess):
        mvp.notificar("Título", "Corpo")
        cmd = mock_subprocess.call_args[0][0]
        # v3.0: runna como sudo -u sant notify-send para acessar D-Bus do usuário
        assert "notify-send" in cmd
        assert "Título" in cmd

    def test_urgencia_customizada(self, mock_subprocess):
        mvp.notificar("T", "C", urgencia="low")
        assert "--urgency=low" in mock_subprocess.call_args[0][0]

    def test_excecao_silenciosa(self, mock_subprocess):
        mock_subprocess.side_effect = FileNotFoundError("not found")
        try:
            mvp.notificar("T", "C")
        except Exception as e:
            pytest.fail(f"notificar propagou exceção: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 8. buscar_devices — por Vendor/Product ID
# ─────────────────────────────────────────────────────────────────────────────

class TestBuscarDevices:

    EV_KEY    = 1
    KEY_ENTER = 28

    def _make_device(self, nome: str, vendor: int = 0x1915,
                     product: int = 0x1025, tem_enter: bool = True) -> MagicMock:
        dev = MagicMock()
        dev.name = nome
        dev.info.vendor  = vendor
        dev.info.product = product
        caps = {self.EV_KEY: [self.KEY_ENTER, 105, 106, 103, 108]} if tem_enter else {}
        dev.capabilities.return_value = caps
        return dev

    def test_detecta_teclado_e_consumer(self):
        tecl = self._make_device("XING WEI 2.4G USB USB Composite Device")
        cons = self._make_device("XING WEI 2.4G USB USB Composite Device Consumer Control")

        with patch("mvp.list_devices", return_value=["/dev/input/event11", "/dev/input/event13"]):
            with patch("mvp.InputDevice", side_effect=[tecl, cons]):
                t, c = mvp.buscar_devices()

        assert t is tecl
        assert c is cons

    def test_ignora_vendor_diferente(self):
        """Device com vendor errado (não XING WEI) deve ser ignorado."""
        outro = self._make_device("2.4G Wireless Device", vendor=0x9999, product=0x0001)

        with patch("mvp.list_devices", return_value=["/dev/input/event10"]):
            with patch("mvp.InputDevice", return_value=outro):
                t, c = mvp.buscar_devices()

        assert t is None
        assert c is None

    def test_ignora_device_sem_key_enter(self):
        """Dois devices mesmo vendor: só o que tem KEY_ENTER é selecionado."""
        fantasma = self._make_device("XING WEI 2.4G USB USB Composite Device", tem_enter=False)
        real     = self._make_device("XING WEI 2.4G USB USB Composite Device", tem_enter=True)

        with patch("mvp.list_devices", return_value=["/dev/input/event15", "/dev/input/event11"]):
            with patch("mvp.InputDevice", side_effect=[fantasma, real]):
                t, _ = mvp.buscar_devices()

        assert t is real

    def test_falha_sem_teclado(self):
        cons = self._make_device("XING WEI 2.4G USB USB Composite Device Consumer Control")

        with patch("mvp.list_devices", return_value=["/dev/input/event13"]):
            with patch("mvp.InputDevice", return_value=cons):
                t, _ = mvp.buscar_devices()

        assert t is None

    def test_permission_error_nao_trava(self):
        with patch("mvp.list_devices", return_value=["/dev/input/event0"]):
            with patch("mvp.InputDevice", side_effect=PermissionError("acesso negado")):
                t, c = mvp.buscar_devices()
        assert t is None
