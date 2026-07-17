# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from evdev import ecodes
from rgb_daemon.main import listener_teclado, listener_consumer

class DummyEvent:
    def __init__(self, type, code, value):
        self.type = type
        self.code = code
        self.value = value

class TestDaemonDispatcher(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.use_cases = MagicMock()
        self.use_cases.state = MagicMock()
        self.use_cases.state.is_active = True
        self.stop_ev = asyncio.Event()

    @patch('asyncio.get_event_loop')
    async def test_listener_teclado_volume_navigation(self, mock_loop):
        """Valida se Volume no Teclado (redundancia) chama as cores certas."""
        dev = MagicMock()
        # Simula eventos de Volume Up e Down no teclado
        events = [
            DummyEvent(ecodes.EV_KEY, ecodes.KEY_VOLUMEUP, 1),
            DummyEvent(ecodes.EV_KEY, ecodes.KEY_VOLUMEDOWN, 1)
        ]
        dev.async_read_loop.return_value.__aiter__.return_value = events
        
        # Faz o loop parar apos ler os eventos
        async def stop_soon():
            await asyncio.sleep(0.1)
            self.stop_ev.set()
        
        asyncio.create_task(stop_soon())
        await listener_teclado(dev, self.use_cases, self.stop_ev)
        
        self.use_cases.next_color.assert_called_once()
        self.use_cases.prev_color.assert_called_once()

    async def test_listener_consumer_mic_toggle(self):
        """Valida se o botao Microfone (582) dispara o toggle_mode."""
        dev = MagicMock()
        KEY_MIC = 582
        events = [DummyEvent(ecodes.EV_KEY, KEY_MIC, 1)]
        dev.async_read_loop.return_value.__aiter__.return_value = events
        
        # Agenda a parada para logo após o processamento
        async def stop_after_delay():
            await asyncio.sleep(0.05)
            self.stop_ev.set()
        
        asyncio.create_task(stop_after_delay())
        await listener_consumer(dev, self.use_cases, None, self.stop_ev)
        
        self.use_cases.toggle_mode.assert_called_once()

    async def test_listener_consumer_volume_navigation(self):
        """Valida se Volume no Consumer Control navega para cores."""
        dev = MagicMock()
        events = [
            DummyEvent(ecodes.EV_KEY, ecodes.KEY_VOLUMEUP, 1),
            DummyEvent(ecodes.EV_KEY, ecodes.KEY_VOLUMEDOWN, 1)
        ]
        dev.async_read_loop.return_value.__aiter__.return_value = events
        
        async def stop_after_delay():
            await asyncio.sleep(0.05)
            self.stop_ev.set()
        
        asyncio.create_task(stop_after_delay())
        await listener_consumer(dev, self.use_cases, None, self.stop_ev)
        
        self.use_cases.next_color.assert_called_once()
        self.use_cases.prev_color.assert_called_once()

if __name__ == '__main__':
    unittest.main()
