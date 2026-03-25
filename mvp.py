#!/usr/bin/env python3
"""
mvp.py — Controle de LEDs via Air Mouse LE-7278  (v2.4)
======================================================
Versão com execução de comando via usuário local (sant).

Novidades:
  • Execução via Usuário: Chama rbg.sh como usuário 'sant' (sudo -u sant).
  • Melhor Compatibilidade: Garante que os drivers/D-Bus/ambiente batam com o terminal.
  • Ativação Instantânea: Botão MIC (VoiceCommand) ou Home.
  • Silenciador DBus: Ignora erros de notificação em modo sudo.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

from evdev import InputDevice, ecodes, list_devices  # type: ignore[import]

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

XINGWEI_VENDOR:  int = 0x1915
XINGWEI_PRODUCT: int = 0x1025
LONG_PRESS_TIME: float = 3.0
OPENRGB_DEVICE:  int = 0

# Paleta com nomes que o rbg.sh reconhece
PALETA: list[tuple[str, str]] = [
    ("Vermelho", "FF0000"), ("Laranja",  "FF5500"), ("Amarelo",  "FFFF00"),
    ("Verde",    "00FF00"), ("Ciano",    "00F2EA"), ("Azul",     "0000FF"),
    ("Roxo",     "AA00FF"), ("Ambar",    "FFB200"), ("Branco",   "FFFFFF"),
    ("Desligar", "000000"),
]

BASE_DIR:    Path = Path(__file__).parent
PID_FILE:    Path = BASE_DIR / ".controle_led.pid"
STATUS_FILE: Path = BASE_DIR / ".controle_led.status"
LOG_DIR:     Path = Path.home() / ".cache" / "controle_led"
LOG_FILE:    Path = LOG_DIR / "controle_led.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("controle_led")

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO E LÓGICA
# ─────────────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class EstadoDaemon:
    modo_led_ativo: bool = False
    indice_cor: int = 8
    ok_press_time: Optional[float] = None
    grabbed: bool = False

def notificar(titulo: str, corpo: str, urgencia: str = "normal") -> None:
    """Envia notificação via desktop (libnotify)."""
    try:
        # Silencia stderr para evitar mensagens de erro de DBus no terminal (em modo sudo)
        subprocess.run(
            ["notify-send", titulo, corpo, f"--urgency={urgencia}", "-t", "2000"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except: pass

def buscar_devices() -> tuple[Optional[InputDevice], Optional[InputDevice]]:
    log.info("🔍 Buscando Air Mouse (1915:1025)...")
    tecl, cons = None, None
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.info.vendor == XINGWEI_VENDOR and dev.info.product == XINGWEI_PRODUCT:
                n = dev.name.lower()
                if "consumer" in n: cons = dev; log.info("  ✅ Consumer → %s", path)
                elif "teclado" in n or "composite device" in n:
                    if ecodes.KEY_ENTER in dev.capabilities().get(1, []):
                        tecl = dev; log.info("  ✅ Teclado  → %s", path)
        except: pass
    return tecl, cons

def aplicar_cor(hex_cor: str, nome: str) -> bool:
    """Aplica a cor rodando o script como o usuário 'sant' para garantir o sucesso do terminal."""
    script_path = BASE_DIR / "rbg.sh"
    # Garante minúsculas e mapeia nomes especiais para o rbg.sh
    nome_cor = nome.lower().replace("desligar", "off").replace("âmbar", "ambar")
    
    if script_path.exists():
        try:
            # Chama o rbg.sh como usuário 'sant' (mesmo que o daemon rode como root)
            # Isso replica exatamente o sucesso do comando no terminal
            cmd = ["sudo", "-u", "sant", "bash", str(script_path), nome_cor]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                log.info("🎨 %s (via rbg.sh as sant)", nome); return True
            else:
                log.error("❌ Erro no script: %s", res.stderr.strip())
        except Exception as e:
            log.error("❌ Exceção ao rodar script: %s", e)

    # Fallback se o script não existir ou falhar drasticamente
    cmd_fallback = ["openrgb", "--device", str(OPENRGB_DEVICE), "--mode", "static", "--color", hex_cor.lstrip("#")]
    try:
        if subprocess.run(cmd_fallback, capture_output=True).returncode == 0:
            log.info("🎨 %s (fallback openrgb)", nome); return True
    except: pass
    return False

def mudar_cor(estado: EstadoDaemon, delta: int) -> None:
    estado.indice_cor = (estado.indice_cor + delta) % len(PALETA)
    n, h = PALETA[estado.indice_cor]
    if aplicar_cor(h, n):
        notificar("🎨 Cor", n, "low")

def alternar_modo(estado: EstadoDaemon, dev_tecl: Optional[InputDevice]) -> None:
    estado.modo_led_ativo = not estado.modo_led_ativo
    if estado.modo_led_ativo:
        log.info("✅ MODO LED ATIVO")
        if dev_tecl:
            try: dev_tecl.grab(); estado.grabbed = True
            except: log.warning("⚠️ Grab falhou")
        STATUS_FILE.write_text("on")
        notificar("🎨 MODO LED", "Ativo")
    else:
        log.info("🔕 MODO LED DESATIVADO")
        if dev_tecl and estado.grabbed:
            try: dev_tecl.ungrab(); estado.grabbed = False
            except: pass
        STATUS_FILE.write_text("off")
        notificar("🔕 MODO LED", "Desativado", "low")

# ─────────────────────────────────────────────────────────────────────────────
# LISTENERS
# ─────────────────────────────────────────────────────────────────────────────

async def listener_teclado(dev: InputDevice, estado: EstadoDaemon, stop_ev: asyncio.Event):
    log.info("🎹 Listener Teclado pronto")
    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY: continue
        
        if ev.code == ecodes.KEY_ENTER:
            if ev.value == 1:
                estado.ok_press_time = asyncio.get_event_loop().time()
            elif ev.value == 0 and estado.ok_press_time is not None:
                dur = asyncio.get_event_loop().time() - estado.ok_press_time
                estado.ok_press_time = None
                if dur >= LONG_PRESS_TIME: alternar_modo(estado, dev)
        
        elif ev.value == 1 and estado.modo_led_ativo:
            if ev.code in (ecodes.KEY_RIGHT, ecodes.KEY_UP): mudar_cor(estado, +1)
            elif ev.code in (ecodes.KEY_LEFT, ecodes.KEY_DOWN): mudar_cor(estado, -1)

async def listener_consumer(dev: InputDevice, estado: EstadoDaemon, dev_tecl: Optional[InputDevice], stop_ev: asyncio.Event):
    log.info("🎛️  Listener Consumer pronto")
    KEY_MIC = 582
    KEY_HOME_ALT = 172

    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY or ev.value != 1: continue
        
        if ev.code in (KEY_MIC, KEY_HOME_ALT):
            log.info("⚡ Botão especial detectado (%d) → Toggle MODO LED", ev.code)
            alternar_modo(estado, dev_tecl)
            continue

        if not estado.modo_led_ativo: continue
        
        if ev.code == ecodes.KEY_VOLUMEUP: mudar_cor(estado, +1)
        elif ev.code == ecodes.KEY_VOLUMEDOWN: mudar_cor(estado, -1)
        elif ev.code == ecodes.KEY_BACK: alternar_modo(estado, dev_tecl)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def run_daemon(dev_tecl: InputDevice, dev_cons: Optional[InputDevice]):
    estado = EstadoDaemon()
    stop_ev = asyncio.Event()
    loop = asyncio.get_event_loop()
    def _on_sig(s):
        if s == signal.SIGUSR1: alternar_modo(estado, dev_tecl)
        else: stop_ev.set()
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1):
        loop.add_signal_handler(s, _on_sig, s)
    
    tasks = [asyncio.create_task(listener_teclado(dev_tecl, estado, stop_ev))]
    if dev_cons: tasks.append(asyncio.create_task(listener_consumer(dev_cons, estado, dev_tecl, stop_ev)))
    
    await stop_ev.wait()
    for t in tasks: t.cancel()
    if estado.grabbed:
        try: dev_tecl.ungrab()
        except: pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toggle", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--list",   action="store_true")
    args = parser.parse_args()

    if args.toggle:
        if not PID_FILE.exists(): print("❌ Off"); sys.exit(1)
        os.kill(int(PID_FILE.read_text()), signal.SIGUSR1); return
    if args.status:
        s = STATUS_FILE.read_text() if STATUS_FILE.exists() else "off"
        print(f"MODO LED: {s.upper()}"); return
    if args.list: buscar_devices(); return

    log.info("🎨 CONTROLE DE LEDs v2.4")
    dev_tecl, dev_cons = buscar_devices()
    if not dev_tecl: sys.exit(1)

    PID_FILE.write_text(str(os.getpid()))
    STATUS_FILE.write_text("off")
    try: asyncio.run(run_daemon(dev_tecl, dev_cons))
    except KeyboardInterrupt: pass
    finally:
        PID_FILE.unlink(missing_ok=True)
        STATUS_FILE.unlink(missing_ok=True)
        log.info("⏹️ Daemon encerrado.")

if __name__ == "__main__":
    main()
