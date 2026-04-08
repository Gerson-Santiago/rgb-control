import pytest
import os
from unittest.mock import MagicMock, patch
from rgb_control.backend import Backend
from rgb_control.window import MainWindow

@pytest.mark.integration
def test_daemon_gui_status_sync(app_instance, fake_filesystem):
    """
    Testa o 'Contrato' entre Daemon e GUI:
    1. Se o Daemon escreve no arquivo de status, a GUI deve ler corretamente.
    """
    status_file = "/tmp/.controle_led.status"
    pid_file = "/tmp/.controle_led.pid"
    
    # Simula Daemon Ativo e em Modo ON
    fake_filesystem.create_file(status_file, contents="on")
    fake_filesystem.create_file(pid_file, contents="1234")
    
    # Mock do backend para usar os arquivos do fake_filesystem através das constantes
    with patch('rgb_control.backend.Backend.STATUS_FILE', status_file), \
         patch('rgb_control.backend.Backend.PID_FILE', pid_file), \
         patch('rgb_control.backend.subprocess.run') as mock_run:
        
        backend = Backend()
        # Mock do systemctl is-active para o backend
        mock_run.return_value = MagicMock(stdout="active", returncode=0)
        
        assert backend.is_service_active() is True
        assert backend.is_led_mode_active() is True
        
        # Agora testa se a Janela reflete isso
        win = MainWindow(application=app_instance)
        # Mock do spinner para não dar erro
        win.fan_spinner = MagicMock()
        
        win.update_status_ui()
        assert win.switch_svc.get_active() is True
        assert win.switch_mode.get_active() is True
        
        # Simula Daemon mudando para OFF no disco
        with open(status_file, "w") as f:
            f.write("off")
            
        win.update_status_ui()
        assert win.switch_mode.get_active() is False

@pytest.mark.integration
def test_gui_signals_daemon_toggle(app_instance, fake_filesystem):
    """Verifica se o clique na GUI envia o sinal SIGUSR1 para o PID do Daemon."""
    pid_file = "/tmp/.controle_led.pid"
    status_file = "/tmp/.controle_led.status"
    fake_filesystem.create_file(pid_file, contents="9999")
    fake_filesystem.create_file(status_file, contents="on")
    
    with patch('os.kill') as mock_kill, \
         patch('rgb_control.backend.Backend.PID_FILE', pid_file), \
         patch('rgb_control.backend.Backend.STATUS_FILE', status_file):
        
        backend = Backend()
        backend.set_led_mode(True) # Isso deve disparar o sinal se o PID existe
        
        mock_kill.assert_called_with(9999, 10) # 10 is SIGUSR1
