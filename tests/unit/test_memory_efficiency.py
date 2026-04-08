import pytest
import gc
import tracemalloc
from unittest.mock import MagicMock, patch
from rgb_control.window import MainWindow

@pytest.mark.slow
def test_ui_update_memory_stability(app_instance):
    """
    Testa se 100 atualizações consecutivas da UI causam crescimento linear de memória.
    Utiliza tracemalloc para capturar snapshots.
    """
    # Mock do backend para não disparar processos reais
    with patch('rgb_control.window.Backend') as mock_backend:
        backend_inst = mock_backend.return_value
        backend_inst.get_current_color.return_value = "#FF0000"
        backend_inst.is_service_active.return_value = True
        backend_inst.is_led_mode_active.return_value = True
        
        win = MainWindow(application=app_instance)
        
        # Aquecimento (Warm-up) para carregar buffers iniciais do GTK
        for _ in range(5):
            win.update_status_ui()
            win.update_cpu_indicator("#00FF00")
        
        gc.collect()
        tracemalloc.start()
        
        snap1 = tracemalloc.take_snapshot()
        
        # Loop de estresse: simulando 100 atualizações
        for i in range(100):
            win.update_status_ui()
            win.update_cpu_indicator(f"#{i%255:02X}AAAA")
            
        gc.collect()
        snap2 = tracemalloc.take_snapshot()
        
        stats = snap2.compare_to(snap1, 'lineno')
        
        # Se houver um crescimento massivo (> 5KB por ciclo) algo está errado
        total_diff = sum(stat.size_diff for stat in stats)
        
        tracemalloc.stop()
        
        # 500KB é generoso para 100 ciclos de strings e Mocks em GTK (4.5KB/ciclo observado)
        assert total_diff < 500 * 1024, f"Vazamento de memória detectado: {total_diff / 1024:.2f} KB"
