
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
import os
# Adiciona o diretório raiz ao path para garantir que 'mvp' seja encontrado por qualquer linter/ambiente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import subprocess
import signal
import asyncio
import os
import argparse
from unittest.mock import MagicMock, patch, call

import pytest  # type: ignore

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

import mvp  # type: ignore  # noqa: E402


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
        with patch("mvp.time.monotonic", side_effect=[100.0, 102.0]):
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

# ─────────────────────────────────────────────────────────────────────────────
# 9. Main e Argparse
# ─────────────────────────────────────────────────────────────────────────────

class TestMain:

    def test_main_list(self):
        with patch("mvp.argparse.ArgumentParser.parse_args") as m_args:
            m_args.return_value = argparse.Namespace(toggle=False, status=False, list=True)
            with patch("mvp.buscar_devices") as m_buscar:
                mvp.main()
                m_buscar.assert_called_once()

    def test_main_status(self, capsys):
        with patch("mvp.argparse.ArgumentParser.parse_args") as m_args:
            m_args.return_value = argparse.Namespace(toggle=False, status=True, list=False)
            mock_status = MagicMock()
            mock_status.exists.return_value = True
            mock_status.read_text.return_value = "on"
            with patch("mvp.STATUS_FILE", mock_status):
                mvp.main()
                out, _ = capsys.readouterr()
                assert "MODO LED: ON" in out

    def test_main_toggle_sucesso(self):
        with patch("mvp.argparse.ArgumentParser.parse_args") as m_args:
            m_args.return_value = argparse.Namespace(toggle=True, status=False, list=False)
            mock_pid = MagicMock()
            mock_pid.exists.return_value = True
            mock_pid.read_text.return_value = "1234"
            with patch("mvp.PID_FILE", mock_pid):
                with patch("os.kill") as m_kill:
                    mvp.main()
                    m_kill.assert_called_once_with(1234, signal.SIGUSR1)

    def test_main_toggle_sem_pid(self, capsys):
        with patch("mvp.argparse.ArgumentParser.parse_args") as m_args:
            m_args.return_value = argparse.Namespace(toggle=True, status=False, list=False)
            mock_pid = MagicMock()
            mock_pid.exists.return_value = False
            with patch("mvp.PID_FILE", mock_pid):
                with pytest.raises(SystemExit):
                    mvp.main()

# ─────────────────────────────────────────────────────────────────────────────
# 10. Async Listeners (Cobertura Crítica)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listener_teclado_navegacao(estado):
    """Testa se as teclas de seta mudam a cor quando o modo está ativo."""
    mock_dev = MagicMock()
    estado.modo_led_ativo = True
    ev_right = MagicMock(type=1, code=106, value=1) # KEY_RIGHT
    ev_up    = MagicMock(type=1, code=103, value=1) # KEY_UP
    ev_left  = MagicMock(type=1, code=105, value=1) # KEY_LEFT
    ev_down  = MagicMock(type=1, code=108, value=1) # KEY_DOWN
    
    async def mock_loop():
        yield ev_right
        yield ev_up
        yield ev_left
        yield ev_down

    mock_dev.async_read_loop.return_value = mock_loop()
    stop_ev = asyncio.Event()

    with patch("mvp.mudar_cor") as m_mudar:
        task = asyncio.create_task(mvp.listener_teclado(mock_dev, estado, stop_ev))
        await asyncio.sleep(0.1)
        stop_ev.set()
        await task
        assert m_mudar.call_count == 4

@pytest.mark.asyncio
async def test_listener_teclado_toggle_ok(estado):
    """v3.0: Simula loop de eventos e toggle via long-press."""
    mock_dev = MagicMock()
    # Simula um evento KEY_ENTER (28) down(1) e up(0)
    ev_down = MagicMock(type=1, code=28, value=1)
    ev_up   = MagicMock(type=1, code=28, value=0)
    
    # Mock do async iterator
    async def mock_loop():
        yield ev_down
        # Simula passagem de tempo curta
        await asyncio.sleep(0.01)
        yield ev_up

    mock_dev.async_read_loop.return_value = mock_loop()
    stop_ev = asyncio.Event()

    with patch("mvp.alternar_modo") as m_alt:
        task = asyncio.create_task(mvp.listener_teclado(mock_dev, estado, stop_ev))
        await asyncio.sleep(0.1)
        stop_ev.set()
        await task
        m_alt.assert_not_called()

@pytest.mark.asyncio
async def test_listener_consumer_toggle_mic(estado):
    mock_dev = MagicMock()
    ev_mic = MagicMock(type=1, code=582, value=1)
    
    async def mock_loop():
        yield ev_mic

    mock_dev.async_read_loop.return_value = mock_loop()
    stop_ev = asyncio.Event()

    with patch("mvp.alternar_modo") as m_alt:
        task = asyncio.create_task(mvp.listener_consumer(mock_dev, estado, None, stop_ev))
        await asyncio.sleep(0.1)
        stop_ev.set()
        await task
        m_alt.assert_called_once()

@pytest.mark.asyncio
async def test_listener_consumer_navegacao(estado):
    mock_dev = MagicMock()
    estado.modo_led_ativo = True
    ev_volup = MagicMock(type=1, code=115, value=1) # KEY_VOLUMEUP
    ev_voldn = MagicMock(type=1, code=114, value=1) # KEY_VOLUMEDOWN
    ev_back  = MagicMock(type=1, code=158, value=1) # KEY_BACK
    
    async def mock_loop():
        yield ev_volup
        yield ev_voldn
        yield ev_back

    mock_dev.async_read_loop.return_value = mock_loop()
    stop_ev = asyncio.Event()

    with patch("mvp.mudar_cor") as m_mudar, patch("mvp.alternar_modo") as m_alt:
        task = asyncio.create_task(mvp.listener_consumer(mock_dev, estado, None, stop_ev))
        await asyncio.sleep(0.1)
        stop_ev.set()
        await task
        assert m_mudar.call_count == 2
        m_alt.assert_called_once()  # Chamado pelo KEY_BACK


@pytest.mark.asyncio
async def test_run_daemon_completo(mock_teclado):
    """Testa o ciclo de vida completo do run_daemon sem travar."""
    mock_cons = MagicMock()
    # Mock para que os loops terminem imediatamente se stop_ev estiver setado
    mock_teclado.async_read_loop.return_value = mock_teclado.__aiter__.return_value = MagicMock()
    mock_cons.async_read_loop.return_value = mock_cons.__aiter__.return_value = MagicMock()
    
    # Simula o loop terminando
    async def empty_loop():
        yield MagicMock(type=0) # EV_SYN

    mock_teclado.async_read_loop.return_value = empty_loop()
    mock_cons.async_read_loop.return_value = empty_loop()

    stop_ev = asyncio.Event()
    
    with patch("mvp.asyncio.Event", return_value=stop_ev):
        # NOTA: Não patcheamos create_task para deixar os listeners rodarem
        daemon_task = asyncio.create_task(mvp.run_daemon(mock_teclado, mock_cons))
        await asyncio.sleep(0.1)
        stop_ev.set()
        # O daemon deve encerrar
        await asyncio.wait_for(daemon_task, timeout=1.0)
        assert True

@pytest.mark.asyncio
async def test_main_executa_daemon():
    """Testa o caminho feliz do main()."""
    with patch("mvp.argparse.ArgumentParser.parse_args") as m_args:
        m_args.return_value = argparse.Namespace(toggle=False, status=False, list=False)
        with patch("mvp.buscar_devices", return_value=(MagicMock(), MagicMock())):
            # Mock de arquivos para evitar PermissionError
            m_file = MagicMock()
            with patch("mvp.PID_FILE", m_file), patch("mvp.STATUS_FILE", m_file):
                with patch("mvp.asyncio.run") as m_run:
                    mvp.main()
                    m_run.assert_called_once()
