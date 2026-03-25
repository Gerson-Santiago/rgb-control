#!/usr/bin/env python3
"""
🎨 CONTROLE DE LEDs — Air Mouse LE-7278
===============================================
Ativa MODO LED:  segurar OK por 3s
Navegar cores:   Vol+ / Vol-  ou  Setas ← → ↑ ↓
Desativar:       segurar OK por 3s  ou  Back
"""

import threading
import time
import subprocess
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

# evdev é um pacote do sistema (sudo apt install python3-evdev)
# O type checker pode não resolver o caminho — é um falso positivo seguro de ignorar.
from evdev import InputDevice, ecodes, list_devices  # type: ignore[import]


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Paleta de cores (cíclica) — edite à vontade!
PALETA = [
    ("Vermelho",  "FF0000"),
    ("Laranja",   "FF5500"),
    ("Amarelo",   "FFFF00"),
    ("Verde",     "00FF00"),
    ("Ciano",     "00F2EA"),
    ("Azul",      "0000FF"),
    ("Roxo",      "AA00FF"),
    ("Âmbar",     "FFB200"),
    ("Branco",    "FFFFFF"),
    ("Desligar",  "000000"),
]

LONG_PRESS_TIME = 3.0   # segundos para ativar/desativar MODO LED
OPENRGB_DEVICE  = 0     # ID do device no OpenRGB

# =============================================================================
# LOGGING
# =============================================================================

LOG_DIR  = Path.home() / ".cache" / "controle_led"
LOG_FILE = LOG_DIR / "controle_led.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("controle_led")

# =============================================================================
# ESTADO GLOBAL
# =============================================================================

modo_led_ativo: bool = False
indice_cor:     int  = 8        # começa em Branco
lock = threading.Lock()
ok_press_time: Optional[float] = None

device_teclado:  Optional[InputDevice] = None
device_consumer: Optional[InputDevice] = None

# =============================================================================
# AUTO-DETECÇÃO
# =============================================================================

def buscar_devices() -> bool:
    """
    Detecta automaticamente os dois devices do Air Mouse (USB dongle).
    Procura por 'xing wei' ou '2.4g' no nome do device.
    """
    global device_teclado, device_consumer

    log.info("🔍 Buscando Air Mouse LE-7278...")

    for path in list_devices():
        try:
            dev  = InputDevice(path)
            nome = dev.name.lower()

            if not any(x in nome for x in ("xing wei", "lelong", "2.4g")):
                continue

            if "consumer control" in nome:
                device_consumer = dev
                log.info(f"  ✅ Consumer Control → {path}  ({dev.name})")

            elif "system control" not in nome:
                device_teclado = dev
                log.info(f"  ✅ Teclado         → {path}  ({dev.name})")

        except Exception:
            pass

    if not device_teclado:
        log.error("❌ Teclado not found. Conecte o Air Mouse e tente novamente.")
        log.error("   Devices disponíveis:")
        for path in list_devices():
            try:
                log.error(f"     {path}: {InputDevice(path).name}")
            except Exception:
                pass
        return False

    if not device_consumer:
        log.warning("⚠️  Consumer Control não encontrado — Vol+/Vol- desabilitado.")

    return True

# =============================================================================
# NOTIFICAÇÕES DESKTOP
# =============================================================================

def notificar(titulo: str, corpo: str, urgencia: str = "normal", ms: int = 3000):
    """Envia notificação via notify-send (libnotify)."""
    try:
        subprocess.run(
            ["notify-send", titulo, corpo,
             f"--urgency={urgencia}",
             f"--expire-time={ms}",
             "--icon=preferences-color"],
            check=False,
            timeout=2,
        )
    except Exception as e:
        log.warning(f"notify-send falhou: {e}")

# =============================================================================
# CONTROLE DE CORES
# =============================================================================

def aplicar_cor(hex_cor: str, nome: str) -> bool:
    """Chama openrgb para aplicar a cor. Tenta sem sudo, depois com sudo."""
    hex_cor = hex_cor.lstrip("#")
    cmd = ["openrgb", "--device", str(OPENRGB_DEVICE),
           "--mode", "static", "--color", hex_cor]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=5)
        if r.returncode == 0:
            log.info(f"🎨  {nome}  #{hex_cor}")
            return True
        # tenta com sudo
        r = subprocess.run(["sudo"] + cmd, capture_output=True, timeout=5)
        if r.returncode == 0:
            log.info(f"🎨  {nome}  #{hex_cor}  (via sudo)")
            return True
    except Exception as e:
        log.error(f"openrgb falhou: {e}")
    return False


def mudar_cor(delta: int):
    """Navega ±1 na paleta e aplica."""
    global indice_cor
    with lock:
        indice_cor = (indice_cor + delta) % len(PALETA)
        nome, cor  = PALETA[indice_cor]
    if aplicar_cor(cor, nome):
        notificar("🎨 Cor", nome, "low", 1500)


def alternar_modo():
    """Liga / desliga MODO LED."""
    global modo_led_ativo
    with lock:
        modo_led_ativo = not modo_led_ativo
        estado = modo_led_ativo                 # captura antes de sair do lock

    if estado:
        log.info("✅ MODO LED: LIGADO")
        notificar(
            "🎨 MODO LED", "Ligado — use Vol+/Vol- ou Setas para mudar as cores",
            "normal", 3000,
        )
    else:
        log.info("🔕 MODO LED: DESLIGADO")
        notificar("🔕 MODO LED", "Desligado", "low", 2000)

# =============================================================================
# THREAD 1 — Teclado (event11)
#   • KEY_ENTER  long press 3s → alternar MODO LED
#   • KEY_RIGHT / KEY_UP       → próxima cor  (só em MODO LED)
#   • KEY_LEFT  / KEY_DOWN     → cor anterior (só em MODO LED)
# =============================================================================

def thread_teclado():
    global ok_press_time

    if not device_teclado:
        return

    log.info(f"🎹 Listener Teclado pronto  [{device_teclado.name}]")

    for ev in device_teclado.read_loop():
        if ev.type != ecodes.EV_KEY:
            continue

        # ── Long press OK ───────────────────────────────────────────
        if ev.code == ecodes.KEY_ENTER:
            if ev.value == 1:                       # pressiona
                ok_press_time = time.time()
            elif ev.value == 0 and ok_press_time:   # solta
                duracao = time.time() - ok_press_time
                ok_press_time = None
                if duracao >= LONG_PRESS_TIME:
                    log.info(f"🔘 Long press OK ({duracao:.1f}s) → alternar modo")
                    alternar_modo()

        # ── Setas (somente em MODO LED, apenas no press inicial) ────
        elif ev.value == 1 and modo_led_ativo:
            if ev.code in (ecodes.KEY_RIGHT, ecodes.KEY_UP):
                log.debug("→ próxima cor")
                mudar_cor(+1)
            elif ev.code in (ecodes.KEY_LEFT, ecodes.KEY_DOWN):
                log.debug("← cor anterior")
                mudar_cor(-1)

# =============================================================================
# THREAD 2 — Consumer Control (event23)
#   • KEY_VOLUMEUP   → próxima cor  (só em MODO LED)
#   • KEY_VOLUMEDOWN → cor anterior (só em MODO LED)
#   • KEY_BACK       → desativar MODO LED imediatamente
# =============================================================================

def thread_consumer():
    if not device_consumer:
        return

    log.info(f"🎛️  Listener Consumer pronto  [{device_consumer.name}]")

    for ev in device_consumer.read_loop():
        if ev.type != ecodes.EV_KEY or ev.value != 1:
            continue

        if ev.code == ecodes.KEY_VOLUMEUP and modo_led_ativo:
            log.debug("Vol+ → próxima cor")
            mudar_cor(+1)

        elif ev.code == ecodes.KEY_VOLUMEDOWN and modo_led_ativo:
            log.debug("Vol- → cor anterior")
            mudar_cor(-1)

        elif ev.code == ecodes.KEY_BACK and modo_led_ativo:
            log.info("⬅️  Back → desativar MODO LED")
            alternar_modo()

# =============================================================================
# MAIN
# =============================================================================

def main():
    log.info("=" * 65)
    log.info("🎨 CONTROLE DE LEDs — Air Mouse LE-7278")
    log.info("=" * 65)

    if not buscar_devices():
        sys.exit(1)

    log.info("")
    log.info("Atalhos:")
    log.info("  Segurar OK (3s)    →  Ativar / Desativar MODO LED")
    log.info("  Vol+ / Seta →/↑   →  Próxima cor  (MODO LED ativo)")
    log.info("  Vol- / Seta ←/↓   →  Cor anterior (MODO LED ativo)")
    log.info("  Back               →  Desativar MODO LED")
    log.info(f"  Log: {LOG_FILE}")
    log.info("  Ctrl+C para sair")
    log.info("")

    t1 = threading.Thread(target=thread_teclado,  daemon=True, name="Teclado")
    t2 = threading.Thread(target=thread_consumer, daemon=True, name="Consumer")

    t1.start()
    if device_consumer:
        t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("\n⏹️  Daemon encerrado.")
        sys.exit(0)


if __name__ == "__main__":
    main()
