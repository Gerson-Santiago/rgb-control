#!/usr/bin/env python3
"""
mvp.py — Controle de LEDs via Air Mouse LE-7278  (v3.0)
======================================================
Daemon Python para controlar LEDs de gabinete (OpenRGB)
com um Air Mouse XING WEI 2.4G USB (Vendor:1915, Product:1025).

Ativação: pressione o botão MIC ou HOME no controle.
Navegação: Seta Direita/Vol+ = próxima cor | Seta Esquerda/Vol- = anterior.
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
import time  # Fornece o relógio monotonic para debounce
from pathlib import Path
from typing import Optional

from evdev import InputDevice, ecodes, list_devices  # type: ignore[import]

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

XINGWEI_VENDOR:  int = 0x1915
XINGWEI_PRODUCT: int = 0x1025
LONG_PRESS_TIME: float = 3.0   # Segundos para o fallback de long-press no OK
OPENRGB_DEVICE:  int = 0

# Paleta de cores — nomes em português batem com o dicionário do rbg.sh
PALETA: list[tuple[str, str]] = [
    ("Vermelho", "FF0000"), ("Laranja",  "FF5500"), ("Amarelo",  "FFFF00"),
    ("Verde",    "00FF00"), ("Ciano",    "00F2EA"), ("Azul",     "0000FF"),
    ("Roxo",     "AA00FF"), ("Ambar",    "FFB200"), ("Branco",   "FFFFFF"),
    ("Desligar", "000000"),
]

BASE_DIR:    Path = Path(__file__).parent.parent.parent # Root dir
PID_FILE:    Path = Path("/tmp/.controle_led.pid")
STATUS_FILE: Path = Path("/tmp/.controle_led.status")
LOG_DIR:     Path = Path.home() / ".cache" / "rgb-control"
LOG_FILE:    Path = LOG_DIR / "daemon.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("controle_led")

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO
# ─────────────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class EstadoDaemon:
    modo_led_ativo: bool = False
    indice_cor: int = 8           # índice inicial = Branco
    ok_press_time: Optional[float] = None
    last_toggle_time: float = 0.0 # Para debounce
    mic_clicks: int = 0           # Contador para Triple Click
    last_click_time: float = 0.0  # Timestamp do último clique
    grabbed: bool = False

# ─────────────────────────────────────────────────────────────────────────────
# OSD / NOTIFICAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

# Endereço do D-Bus da sessão gráfica do usuário (UID 1000 = sant)
# Necessário para notify-send funcionar ao ser chamado via sudo
_DBUS_ADDR = "unix:path=/run/user/1000/bus"

def notificar(titulo: str, corpo: str, urgencia: str = "normal", icone: str = "") -> None:
    """
    Exibe um modal OSD via notify-send (dunst/libnotify).

    Usa 'sudo -u sant env DBUS=...' para acessar o D-Bus da sessão gráfica,
    mesmo quando o daemon está rodando como root.
    Usa x-dunst-stack-tag para substituir a notificação anterior no mesmo
    lugar, criando o efeito de OSD de volume (sem empilhar).
    """
    try:
        subprocess.run(
            ["sudo", "-u", "sant",
             "env", f"DBUS_SESSION_BUS_ADDRESS={_DBUS_ADDR}",
             "notify-send", titulo, corpo,
             f"--urgency={urgencia}", "-t", "3000",
             "-h", "string:x-dunst-stack-tag:modo_led"]
            + (["-i", icone] if icone else []),
            capture_output=True,
        )
    except: pass

# ─────────────────────────────────────────────────────────────────────────────
# LÓGICA DE CORES
# ─────────────────────────────────────────────────────────────────────────────

def buscar_devices() -> tuple[Optional[InputDevice], Optional[InputDevice]]:
    """Detecta teclado e consumer control do Air Mouse pelo Vendor/Product ID."""
    log.info("🔍 Buscando Air Mouse (1915:1025)...")
    tecl, cons = None, None
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.info.vendor == XINGWEI_VENDOR and dev.info.product == XINGWEI_PRODUCT:
                n = dev.name.lower()
                if "consumer" in n:
                    cons = dev; log.info("  ✅ Consumer → %s", path)
                elif "teclado" in n or "composite device" in n:
                    if ecodes.KEY_ENTER in dev.capabilities().get(1, []):
                        tecl = dev; log.info("  ✅ Teclado  → %s", path)
        except: pass
    return tecl, cons

def aplicar_cor(hex_cor: str, nome: str) -> bool:
    """Aplica a cor chamando rbg.sh como usuário 'sant', com fallback para openrgb direto."""
    script_path = BASE_DIR / "rbg.sh"
    # Garante minúsculas — padrão do dicionário COLORS no rbg.sh
    nome_cor = nome.lower().replace("desligar", "off").replace("âmbar", "ambar")

    if script_path.exists():
        try:
            cmd = ["sudo", "-u", "sant", "bash", str(script_path), nome_cor]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                log.info("🎨 %s", nome); return True
            log.warning("⚠️ rbg.sh retornou erro: %s", res.stderr.strip())
        except Exception as e:
            log.error("❌ Exceção ao rodar rbg.sh: %s", e)

    # Fallback: openrgb direto
    cmd_fb = ["openrgb", "--device", str(OPENRGB_DEVICE), "--mode", "static",
               "--color", hex_cor.lstrip("#")]
    try:
        if subprocess.run(cmd_fb, capture_output=True).returncode == 0:
            log.info("🎨 %s (fallback)", nome); return True
    except: pass
    return False

def mudar_cor(estado: EstadoDaemon, delta: int) -> None:
    estado.indice_cor = (estado.indice_cor + delta) % len(PALETA)
    n, h = PALETA[estado.indice_cor]
    if aplicar_cor(h, n):
        notificar(f"🎨 {n}", "Setas navegam | Vol±", "normal", "color-picker")

def alternar_modo(estado: EstadoDaemon, dev_tecl: Optional[InputDevice]) -> None:
    now = time.monotonic()
    if now - estado.last_toggle_time < 0.5:
        return
    estado.last_toggle_time = now

    estado.modo_led_ativo = not estado.modo_led_ativo
    if estado.modo_led_ativo:
        log.info("✅ MODO LED ATIVO")
        if dev_tecl:
            try: dev_tecl.grab(); estado.grabbed = True
            except: log.warning("⚠️ Grab falhou")
        STATUS_FILE.write_text("on")
        # OSD — aparece centralizado como o indicador de volume
        notificar(
            "🟢  MODO LED",
            "ATIVO — use ← → ou Vol± para cores",
            urgencia="normal",
            icone="display-brightness-high",
        )
    else:
        log.info("🔕 MODO LED DESATIVADO")
        if dev_tecl and estado.grabbed:
            try: dev_tecl.ungrab(); estado.grabbed = False
            except: pass
        STATUS_FILE.write_text("off")
        notificar(
            "⚫  MODO LED",
            "MODO LED — Desativado",
            urgencia="normal",
            icone="display-brightness-off",
        )

# ─────────────────────────────────────────────────────────────────────────────
# LISTENERS ASSÍNCRONOS
# ─────────────────────────────────────────────────────────────────────────────

async def listener_teclado(dev: InputDevice, estado: EstadoDaemon, stop_ev: asyncio.Event):
    """Monitora teclado: long-press OK (3s) e setas de navegação."""
    log.info("🎹 Listener Teclado pronto")
    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY: continue

        if ev.code == ecodes.KEY_ENTER:
            if ev.value == 1:
                estado.ok_press_time = asyncio.get_event_loop().time()
            elif ev.value == 0:
                t_press = estado.ok_press_time
                if t_press is not None:
                    dur = asyncio.get_event_loop().time() - t_press
                    estado.ok_press_time = None
                    if dur >= LONG_PRESS_TIME:
                        alternar_modo(estado, dev)

        elif ev.value == 1 and estado.modo_led_ativo:
            if ev.code in (ecodes.KEY_RIGHT, ecodes.KEY_UP):
                mudar_cor(estado, +1)
            elif ev.code in (ecodes.KEY_LEFT, ecodes.KEY_DOWN):
                mudar_cor(estado, -1)

async def listener_consumer(
    dev: InputDevice,
    estado: EstadoDaemon,
    dev_tecl: Optional[InputDevice],
    stop_ev: asyncio.Event,
):
    """Monitora Consumer Control: MIC/HOME toggle, Vol para navegação."""
    log.info("🎛️  Listener Consumer pronto")
    KEY_MIC      = 582   # Botão Voice/Microfone (confirmado em log2.md)
    KEY_HOME_ALT = 172   # Botão Home (confirmado em log2.md)

    async for ev in dev.async_read_loop():
        if stop_ev.is_set(): break
        if ev.type != ecodes.EV_KEY or ev.value != 1: continue

        if ev.code in (KEY_MIC, KEY_HOME_ALT):
            now = time.monotonic()
            if now - estado.last_click_time > 1.0:
                estado.mic_clicks = 1
            else:
                estado.mic_clicks += 1
            estado.last_click_time = now

            if estado.mic_clicks == 1:
                log.info("⚡ Clique detectado (%d)!", ev.code)
                alternar_modo(estado, dev_tecl)
                estado.mic_clicks = 0
            continue

        if not estado.modo_led_ativo: continue

        if ev.code == ecodes.KEY_VOLUMEUP:
            mudar_cor(estado, +1)
        elif ev.code == ecodes.KEY_VOLUMEDOWN:
            mudar_cor(estado, -1)
        elif ev.code == ecodes.KEY_BACK:
            alternar_modo(estado, dev_tecl)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def run_daemon(dev_tecl: InputDevice, dev_cons: Optional[InputDevice]):
    estado = EstadoDaemon()
    stop_ev = asyncio.Event()
    loop = asyncio.get_event_loop()

    def _on_sig(s: int) -> None:
        if s == signal.SIGUSR1:
            alternar_modo(estado, dev_tecl)
        else:
            stop_ev.set()

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1):
        loop.add_signal_handler(s, _on_sig, s)

    tasks = [asyncio.create_task(listener_teclado(dev_tecl, estado, stop_ev))]
    if dev_cons:
        tasks.append(asyncio.create_task(
            listener_consumer(dev_cons, estado, dev_tecl, stop_ev)
        ))

    await stop_ev.wait()
    for t in tasks:
        t.cancel()
    if estado.grabbed:
        try: dev_tecl.ungrab()
        except: pass

def main() -> None:
    parser = argparse.ArgumentParser(description="Controle de LEDs via Air Mouse")
    parser.add_argument("--toggle", action="store_true", help="Alterna MODO LED via SIGUSR1")
    parser.add_argument("--status", action="store_true", help="Mostra estado atual")
    parser.add_argument("--list",   action="store_true", help="Lista devices detectados")
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
        buscar_devices()
        return

    log.info("🎨 CONTROLE DE LEDs v3.0")
    dev_tecl, dev_cons = buscar_devices()
    if not dev_tecl:
        log.error("❌ Teclado Air Mouse não encontrado. Plugue o dongle USB.")
        sys.exit(1)

    PID_FILE.write_text(str(os.getpid()))
    STATUS_FILE.write_text("off")
    try:
        asyncio.run(run_daemon(dev_tecl, dev_cons))
    except KeyboardInterrupt:
        pass
    finally:
        PID_FILE.unlink(missing_ok=True)
        STATUS_FILE.unlink(missing_ok=True)
        log.info("⏹️  Daemon encerrado.")

if __name__ == "__main__":
    main()
