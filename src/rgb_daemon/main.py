#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Callable

from evdev import InputDevice, ecodes, list_devices

from rgb_daemon.domain import DaemonState, PALETTE
from rgb_daemon.application import DaemonUseCases
from rgb_daemon.infrastructure import NotifyOSD, OpenRGBColorApplicator, FileStatusStorage

# Configurações globais
BASE_DIR = Path(__file__).parent.parent.parent
PID_FILE = Path("/tmp/.controle_led.pid")
STATUS_FILE = Path("/tmp/.controle_led.status")
LOG_DIR = Path.home() / ".cache" / "rgb-control"
LOG_FILE = LOG_DIR / "daemon.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("rgb_daemon")

def buscar_devices() -> tuple[Optional[InputDevice], Optional[InputDevice]]:
    log.info("🔍 Buscando Air Mouse (1915:1025)...")
    tecl, cons = None, None
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.info.vendor == 0x1915 and dev.info.product == 0x1025:
                n = dev.name.lower()
                if "consumer" in n:
                    cons = dev; log.info("  ✅ Consumer → %s", path)
                elif "teclado" in n or "composite device" in n:
                    if ecodes.KEY_ENTER in dev.capabilities().get(1, []):
                        tecl = dev; log.info("  ✅ Teclado  → %s", path)
        except Exception: pass
    return tecl, cons

async def listener_teclado(dev: InputDevice, use_cases: DaemonUseCases, stop_ev: asyncio.Event) -> None:
    """Monitora teclado: OK (long-press) e setas/volume para cores."""
    log.info("🎹 Listener Teclado pronto")
    LONG_PRESS_TIME = 3.0
    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY: continue

        # Lógica de Long-Press no OK (Enter)
        if ev.code == ecodes.KEY_ENTER:
            if ev.value == 1:
                use_cases.state.ok_press_time = asyncio.get_event_loop().time()
            elif ev.value == 0:
                t_press = use_cases.state.ok_press_time
                if t_press is not None:
                    dur = asyncio.get_event_loop().time() - t_press
                    use_cases.state.ok_press_time = None
                    if dur >= LONG_PRESS_TIME:
                        use_cases.toggle_mode(dev)

        # Atalhos de Cor (apenas se ativo)
        elif ev.value == 1 and use_cases.state.is_active:
            if ev.code in (ecodes.KEY_RIGHT, ecodes.KEY_UP, ecodes.KEY_VOLUMEUP):
                use_cases.next_color()
            elif ev.code in (ecodes.KEY_LEFT, ecodes.KEY_DOWN, ecodes.KEY_VOLUMEDOWN):
                use_cases.prev_color()

async def listener_consumer(dev: InputDevice, use_cases: DaemonUseCases, dev_tecl: Optional[InputDevice], stop_ev: asyncio.Event) -> None:
    """Monitora Consumer Control: Microfone (toggle) e Volume."""
    log.info("🎛️  Listener Consumer pronto")
    KEY_MIC = 582
    KEY_HOME_ALT = 172

    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        # No consumer, focamos apenas no KEY DOWN (value=1)
        if ev.type != ecodes.EV_KEY or ev.value != 1: continue

        # Toggle via Microfone ou Home
        if ev.code in (KEY_MIC, KEY_HOME_ALT):
            # Clique único ativa/desativa
            use_cases.toggle_mode(dev_tecl)
            continue

        if not use_cases.state.is_active: continue

        # Navegação de cores (Volume e Back)
        if ev.code == ecodes.KEY_VOLUMEUP:
            use_cases.next_color()
        elif ev.code == ecodes.KEY_VOLUMEDOWN:
            use_cases.prev_color()
        elif ev.code == ecodes.KEY_BACK:
            use_cases.toggle_mode(dev_tecl)

def handle_signal(s: int, use_cases: DaemonUseCases, dev_tecl: Optional[InputDevice], status_file: Path, stop_ev: asyncio.Event) -> None:
    """Processa sinais SIGUSR1 (sincronia) e SIGINT/SIGTERM (parada)."""
    if s == signal.SIGUSR1:
        # Sincroniza o estado lendo do arquivo (permite que a GUI force ON/OFF)
        try:
            if status_file.exists():
                status = status_file.read_text().strip()
                use_cases.set_active(status == "on", dev_tecl)
            else:
                use_cases.toggle_mode(dev_tecl)
        except Exception as e:
            log.error("Erro ao processar sinal SIGUSR1: %s", e)
            use_cases.toggle_mode(dev_tecl)
    else:
        stop_ev.set()

async def run_daemon(dev_tecl: InputDevice, dev_cons: Optional[InputDevice], use_cases: DaemonUseCases) -> None:
    stop_ev = asyncio.Event()
    loop = asyncio.get_event_loop()

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1):
        # Usamos uma função nomeada parcial para satisfazer a tipagem estrita
        def create_handler(sig: int) -> Callable[[], None]:
            return lambda: handle_signal(sig, use_cases, dev_tecl, STATUS_FILE, stop_ev)
        loop.add_signal_handler(s, create_handler(s))

    tasks = [asyncio.create_task(listener_teclado(dev_tecl, use_cases, stop_ev))]
    if dev_cons:
        tasks.append(asyncio.create_task(listener_consumer(dev_cons, use_cases, dev_tecl, stop_ev)))

    await stop_ev.wait()
    for t in tasks: t.cancel()
    
    # Garantir que o device seja solto ao encerrar
    if use_cases.state.is_grabbed:
        try: dev_tecl.ungrab()
        except Exception: pass

def main() -> None:
    parser = argparse.ArgumentParser(description="Clean RGB Daemon")
    parser.add_argument("--toggle", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--list",   action="store_true")
    args = parser.parse_args()

    if args.toggle:
        if not PID_FILE.exists():
            print("❌ Daemon não está rodando."); sys.exit(1)
        os.kill(int(PID_FILE.read_text().strip()), signal.SIGUSR1)
        return
    if args.status:
        s = STATUS_FILE.read_text().strip() if STATUS_FILE.exists() else "off"
        print(f"MODO LED: {s.upper()}")
        return
    if args.list:
        buscar_devices(); return

    # Injeção de Dependências
    state = DaemonState()
    osd = NotifyOSD()
    applicator = OpenRGBColorApplicator(device_id=0)
    storage = FileStatusStorage(STATUS_FILE, PID_FILE)
    
    use_cases = DaemonUseCases(state, osd, applicator, storage)

    log.info("🏗️  CONTROLE DE LEDs v3.5 (Clean Architecture)")
    dev_tecl, dev_cons = buscar_devices()
    if not dev_tecl:
        log.error("❌ Teclado não encontrado."); sys.exit(1)

    storage.save_pid(os.getpid())
    storage.save_status("off")
    try:
        asyncio.run(run_daemon(dev_tecl, dev_cons, use_cases))
    except KeyboardInterrupt: pass
    finally:
        PID_FILE.unlink(missing_ok=True)
        STATUS_FILE.unlink(missing_ok=True)
        log.info("⏹️  Daemon encerrado.")

if __name__ == "__main__":
    main()
