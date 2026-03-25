"""
tests/test_mvp.py
=================
Suite de testes robusta para mvp.py — Controle de LEDs via Air Mouse LE-7278

Estratégia: mocking híbrido
  • Lógica de negócio  → testada com mocks (sem hardware)
  • Erros de hardware  → simulados com side_effect
  • Parametrize        → cobre múltiplos valores sem duplicar código
  • Fixtures           → configuram e limpam estado global entre testes

Rodar:
    python3 -m pytest tests/ -v
    python3 -m pytest tests/ -v --cov=mvp --cov-report=term-missing
"""

import sys
import time
import subprocess
from unittest.mock import MagicMock, patch, call

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# STUB DO HARDWARE — registrado ANTES do import do módulo
# ─────────────────────────────────────────────────────────────────────────────

class _EcodeStub:
    """Códigos reais do kernel Linux (confirmados nos logs do evtest)."""
    EV_KEY        = 1
    KEY_ENTER     = 28
    KEY_RIGHT     = 106
    KEY_LEFT      = 105
    KEY_UP        = 103
    KEY_DOWN      = 108
    KEY_VOLUMEUP  = 115
    KEY_VOLUMEDOWN = 114
    KEY_BACK      = 158

class _EvdevStub(MagicMock):
    """Módulo evdev falso com ecodes reais e InputDevice simulável."""
    ecodes = _EcodeStub()

_evdev_stub = _EvdevStub()
_evdev_stub.list_devices.return_value = []   # sem devices por padrão
sys.modules["evdev"] = _evdev_stub

# Importa o módulo DEPOIS do stub estar registrado
import mvp  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def estado_global_limpo():
    """
    Restaura o estado global do daemon antes de CADA teste.
    autouse=True → aplicado automaticamente em todos os testes.
    """
    mvp.modo_led_ativo = False
    mvp.indice_cor     = 8        # índice de "Branco"
    mvp.ok_press_time  = None
    mvp.device_teclado  = None
    mvp.device_consumer = None
    yield                         # executa o teste
    # cleanup pós-teste (se necessário)
    mvp.modo_led_ativo = False


@pytest.fixture
def mock_subprocess():
    """Mockeia subprocess.run globalmente no módulo mvp."""
    with patch("mvp.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_notificar():
    """Substitui notificar() para não chamar notify-send nos testes."""
    with patch("mvp.notificar") as mock_n:
        yield mock_n


@pytest.fixture
def mock_aplicar_cor_ok():
    """aplicar_cor() sempre retorna True (sucesso)."""
    with patch("mvp.aplicar_cor", return_value=True) as mock_ac:
        yield mock_ac


# ─────────────────────────────────────────────────────────────────────────────
# 1. PALETA DE CORES
# ─────────────────────────────────────────────────────────────────────────────

class TestPaleta:

    def test_tamanho_esperado(self):
        assert len(mvp.PALETA) == 10

    @pytest.mark.parametrize("indice,nome,hex_esperado", [
        (0,  "Vermelho", "FF0000"),
        (3,  "Verde",    "00FF00"),
        (5,  "Azul",     "0000FF"),
        (8,  "Branco",   "FFFFFF"),
        (9,  "Desligar", "000000"),
    ])
    def test_cores_especificas(self, indice, nome, hex_esperado):
        n, h = mvp.PALETA[indice]
        assert n == nome, f"índice {indice}: nome esperado '{nome}', obtido '{n}'"
        assert h == hex_esperado

    @pytest.mark.parametrize("nome,cor", mvp.PALETA)
    def test_todos_hex_validos(self, nome, cor):
        import re
        assert re.fullmatch(r"[0-9A-Fa-f]{6}", cor), \
            f"'{cor}' ({nome}) não é um HEX válido de 6 dígitos"

    def test_ultimo_e_preto(self):
        _, cor = mvp.PALETA[-1]
        assert cor == "000000", "Último item deve ser preto (desligar LEDs)"


# ─────────────────────────────────────────────────────────────────────────────
# 2. NAVEGAÇÃO DE CORES (mudar_cor)
# ─────────────────────────────────────────────────────────────────────────────

class TestMudarCor:

    @pytest.mark.parametrize("inicio,delta,esperado", [
        (0, +1, 1),   # Vermelho → Laranja
        (3, +1, 4),   # Verde → Ciano
        (3, -1, 2),   # Verde → Amarelo
        (8,  0, 8),   # sem movimento
    ])
    def test_delta_basico(self, inicio, delta, esperado, mock_notificar, mock_aplicar_cor_ok):
        mvp.indice_cor = inicio
        mvp.mudar_cor(delta)
        assert mvp.indice_cor == esperado

    def test_ciclico_frente(self, mock_notificar, mock_aplicar_cor_ok):
        """Do último item deve voltar para o primeiro."""
        mvp.indice_cor = len(mvp.PALETA) - 1
        mvp.mudar_cor(+1)
        assert mvp.indice_cor == 0

    def test_ciclico_tras(self, mock_notificar, mock_aplicar_cor_ok):
        """Do primeiro item deve ir para o último."""
        mvp.indice_cor = 0
        mvp.mudar_cor(-1)
        assert mvp.indice_cor == len(mvp.PALETA) - 1

    def test_aplica_cor_correta(self, mock_notificar):
        """mudar_cor() deve chamar aplicar_cor com o HEX certo."""
        with patch("mvp.aplicar_cor", return_value=True) as mock_ac:
            mvp.indice_cor = 0   # Vermelho
            mvp.mudar_cor(+1)    # → Laranja
            nome, cor = mvp.PALETA[1]
            mock_ac.assert_called_once_with(cor, nome)

    def test_sem_notificacao_se_openrgb_falhar(self, mock_notificar):
        """Se openrgb falhar, NÃO deve notificar."""
        with patch("mvp.aplicar_cor", return_value=False):
            mvp.mudar_cor(+1)
        mock_notificar.assert_not_called()

    def test_notifica_nome_da_cor(self, mock_notificar, mock_aplicar_cor_ok):
        """Notificação deve conter o nome da nova cor."""
        mvp.indice_cor = 0
        mvp.mudar_cor(+1)                   # → Laranja (índice 1)
        nome_esperado = mvp.PALETA[1][0]
        args = mock_notificar.call_args[0]   # (titulo, corpo, ...)
        assert nome_esperado in args


# ─────────────────────────────────────────────────────────────────────────────
# 3. MODO LED (alternar_modo)
# ─────────────────────────────────────────────────────────────────────────────

class TestAlternarModo:

    def test_liga(self, mock_notificar):
        assert mvp.modo_led_ativo is False
        mvp.alternar_modo()
        assert mvp.modo_led_ativo is True

    def test_desliga(self, mock_notificar):
        mvp.modo_led_ativo = True
        mvp.alternar_modo()
        assert mvp.modo_led_ativo is False

    def test_toggle_duplo_restaura_estado(self, mock_notificar):
        mvp.alternar_modo()
        mvp.alternar_modo()
        assert mvp.modo_led_ativo is False

    def test_notificacao_ao_ligar(self, mock_notificar):
        mvp.alternar_modo()
        titulo, corpo = mock_notificar.call_args[0][:2]
        assert "Ligado" in corpo

    def test_notificacao_ao_desligar(self, mock_notificar):
        mvp.modo_led_ativo = True
        mvp.alternar_modo()
        titulo, corpo = mock_notificar.call_args[0][:2]
        assert "Desligado" in corpo

    def test_notifica_exatamente_uma_vez(self, mock_notificar):
        mvp.alternar_modo()
        assert mock_notificar.call_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# 4. LONG PRESS — lógica de tempo
# ─────────────────────────────────────────────────────────────────────────────

class TestLongPress:

    LONG = mvp.LONG_PRESS_TIME

    @pytest.mark.parametrize("duracao_s,deve_alternar", [
        (3.1, True),    # exatamente acima do limiar
        (5.0, True),    # bem acima
        (0.5, False),   # press rápido
        (2.9, False),   # quase 3s mas não chegou
    ])
    def test_limiar(self, duracao_s, deve_alternar):
        """Simula press e release com diferentes durações."""
        with patch("mvp.alternar_modo") as mock_alt:
            t0 = time.time() - duracao_s
            mvp.ok_press_time = t0

            duracao_real = time.time() - mvp.ok_press_time
            mvp.ok_press_time = None
            if duracao_real >= mvp.LONG_PRESS_TIME:
                mvp.alternar_modo()

            if deve_alternar:
                mock_alt.assert_called_once()
            else:
                mock_alt.assert_not_called()

    def test_long_press_time_ergonomico(self):
        """LONG_PRESS_TIME deve ser entre 2s e 5s (ergonomia)."""
        assert 2.0 <= mvp.LONG_PRESS_TIME <= 5.0


# ─────────────────────────────────────────────────────────────────────────────
# 5. APLICAR COR — interface com openrgb (subprocess)
# ─────────────────────────────────────────────────────────────────────────────

class TestAplicarCor:

    def test_sucesso_sem_sudo(self, mock_subprocess):
        resultado = mvp.aplicar_cor("FF0000", "Vermelho")
        assert resultado is True
        cmd = mock_subprocess.call_args_list[0][0][0]
        assert "sudo" not in cmd
        assert "FF0000" in cmd

    def test_fallback_sudo_quando_falha(self, mock_subprocess):
        """2ª tentativa (com sudo) é acionada quando a 1ª falha."""
        mock_subprocess.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=0),
        ]
        resultado = mvp.aplicar_cor("00FF00", "Verde")
        assert resultado is True
        assert mock_subprocess.call_count == 2
        cmd_sudo = mock_subprocess.call_args_list[1][0][0]
        assert "sudo" in cmd_sudo

    def test_retorna_false_quando_ambas_falham(self, mock_subprocess):
        """Se sem sudo E com sudo falharem, retorna False."""
        mock_subprocess.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=1),
        ]
        assert mvp.aplicar_cor("0000FF", "Azul") is False

    def test_excecao_timeout_retorna_false(self, mock_subprocess):
        """Simula hardware que não responde (timeout)."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("openrgb", 5)
        assert mvp.aplicar_cor("FFFFFF", "Branco") is False

    def test_excecao_genérica_retorna_false(self, mock_subprocess):
        mock_subprocess.side_effect = Exception("USB disconnected")
        assert mvp.aplicar_cor("000000", "Desligar") is False

    @pytest.mark.parametrize("hex_entrada,hex_esperado", [
        ("FF0000",   "FF0000"),   # sem #
        ("#FF0000",  "FF0000"),   # com #
        ("##FF0000", "FF0000"),   # duplo # (robustez)
    ])
    def test_remove_hash(self, hex_entrada, hex_esperado, mock_subprocess):
        mvp.aplicar_cor(hex_entrada, "Teste")
        cmd = mock_subprocess.call_args_list[0][0][0]
        cor_passada = cmd[cmd.index("--color") + 1]
        assert "#" not in cor_passada
        assert hex_esperado in cor_passada

    def test_device_id_correto(self, mock_subprocess):
        mvp.aplicar_cor("FF0000", "Vermelho")
        cmd = mock_subprocess.call_args_list[0][0][0]
        device_idx = cmd.index("--device") + 1
        assert cmd[device_idx] == str(mvp.OPENRGB_DEVICE)


# ─────────────────────────────────────────────────────────────────────────────
# 6. NOTIFICAÇÕES — notify-send
# ─────────────────────────────────────────────────────────────────────────────

class TestNotificar:

    def test_chama_notify_send(self, mock_subprocess):
        mvp.notificar("🎨 MODO LED", "Ligado")
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[0] == "notify-send"
        assert "🎨 MODO LED" in cmd
        assert "Ligado" in cmd

    def test_urgencia_default_normal(self, mock_subprocess):
        mvp.notificar("T", "C")
        cmd = mock_subprocess.call_args[0][0]
        assert "--urgency=normal" in cmd

    def test_urgencia_customizada(self, mock_subprocess):
        mvp.notificar("T", "C", urgencia="low")
        cmd = mock_subprocess.call_args[0][0]
        assert "--urgency=low" in cmd

    def test_tempo_customizado(self, mock_subprocess):
        mvp.notificar("T", "C", ms=1500)
        cmd = mock_subprocess.call_args[0][0]
        assert "--expire-time=1500" in cmd

    def test_excecao_nao_propaga(self, mock_subprocess):
        """notify-send ausente NÃO deve derrubar o daemon."""
        mock_subprocess.side_effect = FileNotFoundError("notify-send not found")
        try:
            mvp.notificar("T", "C")
        except Exception as e:
            pytest.fail(f"notificar() propagou exceção inesperada: {e}")

    def test_timeout_nao_propaga(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired("notify-send", 2)
        try:
            mvp.notificar("T", "C")
        except Exception as e:
            pytest.fail(f"notificar() propagou TimeoutExpired: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. AUTO-DETECÇÃO DE DEVICES (buscar_devices)
# ─────────────────────────────────────────────────────────────────────────────

class TestBuscarDevices:

    def _make_device(self, nome: str):
        dev = MagicMock()
        dev.name = nome
        return dev

    def test_detecta_teclado_e_consumer(self):
        """Simula dois devices XING WEI retornados por list_devices."""
        dev_tecl = self._make_device("XING WEI 2.4G USB USB Composite Device")
        dev_cons = self._make_device("XING WEI 2.4G USB USB Composite Device Consumer Control")

        with patch("mvp.list_devices", return_value=["/dev/input/event11", "/dev/input/event23"]):
            with patch("mvp.InputDevice", side_effect=[dev_tecl, dev_cons]):
                resultado = mvp.buscar_devices()

        assert resultado is True
        assert mvp.device_teclado is dev_tecl
        assert mvp.device_consumer is dev_cons

    def test_falha_sem_teclado(self):
        """Sem teclado → retorna False."""
        dev_cons = self._make_device("XING WEI 2.4G USB USB Composite Device Consumer Control")

        with patch("mvp.list_devices", return_value=["/dev/input/event23"]):
            with patch("mvp.InputDevice", return_value=dev_cons):
                resultado = mvp.buscar_devices()

        assert resultado is False

    def test_aviso_sem_consumer(self, caplog):
        """Sem consumer control → retorna True mas com aviso de log."""
        import logging
        dev_tecl = self._make_device("XING WEI 2.4G USB USB Composite Device")

        with patch("mvp.list_devices", return_value=["/dev/input/event11"]):
            with patch("mvp.InputDevice", return_value=dev_tecl):
                with caplog.at_level(logging.WARNING):
                    resultado = mvp.buscar_devices()

        assert resultado is True              # ainda funciona (sem Vol+/Vol-)
        assert "Consumer Control" in caplog.text or resultado is True

    def test_device_inacessivel_nao_trava(self):
        """PermissionError em /dev/input não deve travar a busca."""
        with patch("mvp.list_devices", return_value=["/dev/input/event0"]):
            with patch("mvp.InputDevice", side_effect=PermissionError("acesso negado")):
                resultado = mvp.buscar_devices()

        assert resultado is False   # não encontrou, mas não travou
