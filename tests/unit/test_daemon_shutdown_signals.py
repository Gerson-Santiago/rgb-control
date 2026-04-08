import unittest
import signal
import os
from unittest.mock import MagicMock, patch
from rgb_daemon.main import handle_signal

class TestDaemonShutdownSignals(unittest.TestCase):
    """
    Testes para garantir que o Daemon encerra de forma limpa.
    Seguindo TDD, validamos o comportamento de saída.
    """

    def test_handle_signal_stop_event(self):
        """SIGINT deve disparar o stop_event para encerrar o loop asyncio."""
        mock_use_cases = MagicMock()
        mock_dev = MagicMock()
        mock_status = MagicMock()
        stop_ev = MagicMock()
        
        # Chama com SIGINT (Interrupção)
        handle_signal(signal.SIGINT, mock_use_cases, mock_dev, mock_status, stop_ev)
        
        # Deve chamar set() no evento de parada
        stop_ev.set.assert_called_once()

    def test_handle_signal_sigusr1_sync(self):
        """SIGUSR1 deve disparar a sincronização de estado no UseCases."""
        mock_use_cases = MagicMock()
        mock_dev = MagicMock()
        mock_status = MagicMock()
        stop_ev = MagicMock()
        
        # Simula arquivo de status com "on"
        mock_status.exists.return_value = True
        mock_status.read_text.return_value = "on"
        
        handle_signal(signal.SIGUSR1, mock_use_cases, mock_dev, mock_status, stop_ev)
        
        # Deve atualizar o estado para ativo
        mock_use_cases.set_active.assert_called_with(True, mock_dev)

if __name__ == '__main__':
    unittest.main()
