#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

from evdev import InputDevice, ecodes, list_devices  # type: ignore[import]

from rgb_daemon.domain import DaemonState, PALETTE
from rgb_daemon.application import DaemonUseCases
from rgb_daemon.infrastructure import NotifyOSD, ShellColorApplicator, FileStatusStorage

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

async def listener_teclado(dev: InputDevice, use_cases: DaemonUseCases, stop_ev: asyncio.Event):
    log.info("🎹 Listener Teclado pronto")
    LONG_PRESS_TIME = 3.0
    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY: continue

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

        elif ev.value == 1 and use_cases.state.is_active:
            if ev.code in (ecodes.KEY_RIGHT, ecodes.KEY_UP):
                use_cases.next_color()
            elif ev.code in (ecodes.KEY_LEFT, ecodes.KEY_DOWN):
                use_cases.prev_color()

async def listener_consumer(dev: InputDevice, use_cases: DaemonUseCases, dev_tecl: Optional[InputDevice], stop_ev: asyncio.Event):
    log.info("🎛️  Listener Consumer pronto")
    KEY_MIC = 582
    KEY_HOME_ALT = 172

    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY or ev.value != 1: continue

        if ev.code in (KEY_MIC, KEY_HOME_ALT):
            now = time.monotonic()
            if now - use_cases.state.last_click_time > 1.0:
                use_cases.state.mic_clicks = 1
            else:
                use_cases.state.mic_clicks += 1
            use_cases.state.last_click_time = now

            if use_cases.state.mic_clicks == 1:
                use_cases.toggle_mode(dev_tecl)
                use_cases.state.mic_clicks = 0
            continue

        if not use_cases.state.is_active: continue

        if ev.code == ecodes.KEY_VOLUMEUP:
            use_cases.next_color()
        elif ev.code == ecodes.KEY_VOLUMEDOWN:
            use_cases.prev_color()
        elif ev.code == ecodes.KEY_BACK:
            use_cases.toggle_mode(dev_tecl)

async def run_daemon(dev_tecl: InputDevice, dev_cons: Optional[InputDevice], use_cases: DaemonUseCases):
    stop_ev = asyncio.Event()
    loop = asyncio.get_event_loop()

    def _on_sig(s: int) -> None:
        if s == signal.SIGUSR1:
            use_cases.toggle_mode(dev_tecl)
        else:
            stop_ev.set()

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1):
        loop.add_signal_handler(s, _on_sig, s)

    tasks = [asyncio.create_task(listener_teclado(dev_tecl, use_cases, stop_ev))]
    if dev_cons:
        tasks.append(asyncio.create_task(listener_consumer(dev_cons, use_cases, dev_tecl, stop_ev)))

    await stop_ev.wait()
    for t in tasks: t.cancel()
    if use_cases.state.is_grabbed:
        try: dev_tecl.ungrab()
        except: pass

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
    applicator = ShellColorApplicator(BASE_DIR / "rbg.sh")
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
