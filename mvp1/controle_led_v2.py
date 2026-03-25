#!/usr/bin/env python3
"""
🎨 CONTROLE DE LEDs - Air Mouse LE-7278 (v2)
Modo LED: Long press OK (3s) ativa/desativa
Navegação: Vol+/Vol- ou Setas ←→↑↓ mudam cores (apenas no MODO LED)
Back: desativa o modo
"""

import threading
import time
import subprocess
import sys
import logging
from pathlib import Path
from evdev import InputDevice, ecodes, list_devices
from typing import Optional, Tuple

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Paleta de cores (cíclica)
PALETA = [
    ("Vermelho",   "FF0000"),
    ("Laranja",    "FF5500"),
    ("Amarelo",    "FFFF00"),
    ("Verde",      "00FF00"),
    ("Ciano",      "00F2EA"),
    ("Azul",       "0000FF"),
    ("Roxo",       "AA00FF"),
    ("Ambar",      "FFB200"),
    ("Branco",     "FFFFFF"),
    ("Desligar",   "000000"),
]

# Configuração geral
LONG_PRESS_TIME = 3.0
DEVICE_ID = 0

# Logging
LOG_DIR = Path.home() / ".cache" / "controle_led"
LOG_FILE = LOG_DIR / "controle_led.log"

# ============================================================================
# SETUP LOGGING
# ============================================================================

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ESTADO GLOBAL
# ============================================================================

modo_led_ativo = False
indice_cor = 8  # Começa com Branco
lock = threading.Lock()
ok_press_time = None

# Devices (serão auto-detectados)
device_teclado: Optional[InputDevice] = None
device_consumer: Optional[InputDevice] = None

# ============================================================================
# AUTO-DETECÇÃO DE DEVICES
# ============================================================================

def buscar_devices() -> Tuple[Optional[InputDevice], Optional[InputDevice]]:
    """
    Auto-detecta os devices do Air Mouse LE-7278
    Retorna: (device_teclado, device_consumer)
    """
    logger.info("🔍 Buscando devices do Air Mouse LE-7278...")
    
    teclado = None
    consumer = None
    
    for device_path in list_devices():
        try:
            device = InputDevice(device_path)
            nome_lower = device.name.lower()
            
            # Procura por identificadores do Air Mouse
            if any(x in nome_lower for x in ["xing wei", "lelong", "2.4g"]):
                
                # Identificação por tipo
                if "consumer control" in nome_lower:
                    consumer = device
                    logger.info(f"✅ Consumer Control encontrado: {device_path} - {device.name}")
                
                elif "system control" not in nome_lower:
                    # É o teclado principal (exclui system control)
                    teclado = device
                    logger.info(f"✅ Teclado encontrado: {device_path} - {device.name}")
        
        except Exception as e:
            logger.debug(f"Erro ao verificar {device_path}: {e}")
    
    if not teclado:
        logger.error("❌ Teclado não encontrado!")
    
    if not consumer:
        logger.warning("⚠️  Consumer Control não encontrado (Vol+/Vol- desabilitado)")
    
    return teclado, consumer

# ============================================================================
# NOTIFICAÇÕES DESKTOP
# ============================================================================

def notificar(titulo: str, mensagem: str, urgencia: str = "normal", tempo_ms: int = 3000):
    """Envia notificação desktop com notify-send"""
    try:
        subprocess.run([
            "notify-send",
            titulo,
            mensagem,
            f"--urgency={urgencia}",
            f"--expire-time={tempo_ms}",
            "--icon=preferences-color"
        ], check=False, timeout=2)
    except Exception as e:
        logger.warning(f"Erro ao enviar notificação: {e}")

# ============================================================================
# CONTROLE DE CORES
# ============================================================================

def aplicar_cor(hex_color: str, nome_cor: str) -> bool:
    """Aplica cor aos LEDs usando openrgb"""
    try:
        hex_color = hex_color.lstrip('#')
        
        cmd = [
            "openrgb",
            "--device", str(DEVICE_ID),
            "--mode", "static",
            "--color", hex_color
        ]
        
        # Tenta sem sudo primeiro
        result = subprocess.run(cmd, capture_output=True, timeout=5, check=False)
        
        if result.returncode == 0:
            logger.info(f"🎨 Cor aplicada: {nome_cor} (#{hex_color})")
            return True
        else:
            # Tenta com sudo
            logger.debug(f"Tentando com sudo...")
            result = subprocess.run(
                ["sudo"] + cmd,
                capture_output=True,
                timeout=5,
                check=False
            )
            if result.returncode == 0:
                logger.info(f"🎨 Cor aplicada (sudo): {nome_cor}")
                return True
    
    except Exception as e:
        logger.error(f"Erro ao aplicar cor: {e}")
    
    return False

def mudar_cor(delta: int):
    """Navega na paleta: delta=1 (próxima), delta=-1 (anterior)"""
    global indice_cor
    
    with lock:
        indice_cor = (indice_cor + delta) % len(PALETA)
        nome, cor = PALETA[indice_cor]
        
        if aplicar_cor(cor, nome):
            notificar("🎨 Cor", nome, "low", 1500)

def alternar_modo():
    """Liga/desliga MODO LED com notificação"""
    global modo_led_ativo
    
    with lock:
        modo_led_ativo = not modo_led_ativo
        
        if modo_led_ativo:
            logger.info("✅ MODO LED: LIGADO")
            notificar(
                "🎨 MODO LED",
                "Ligado — use Vol+/Vol- ou Setas para mudar as cores",
                "normal",
                3000
            )
        else:
            logger.info("❌ MODO LED: DESLIGADO")
            notificar(
                "🔕 MODO LED",
                "Desligado",
                "low",
                2000
            )

# ============================================================================
# THREAD 1: LISTENER TECLADO (event11)
# ============================================================================

def thread_teclado():
    """
    Monitora event11 (teclado)
    - Long press OK (3s) → alternar MODO LED
    - Setas ← → ↑ ↓ → navegar cores
    """
    global ok_press_time, device_teclado
    
    if not device_teclado:
        logger.error("Device teclado não disponível!")
        return
    
    logger.info(f"🎹 Listener Teclado iniciado: {device_teclado.name}")
    
    try:
        for event in device_teclado.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            
            keycode = event.code
            value = event.value
            
            # ====== LONG PRESS OK (KEY_ENTER) ======
            if keycode == ecodes.KEY_ENTER:
                if value == 1:  # Pressionado
                    ok_press_time = time.time()
                    logger.debug("OK pressionado")
                
                elif value == 0:  # Solto
                    if ok_press_time:
                        duracao = time.time() - ok_press_time
                        ok_press_time = None
                        
                        if duracao >= LONG_PRESS_TIME:
                            logger.info(f"🔘 Long press OK detectado ({duracao:.1f}s)")
                            alternar_modo()
            
            # ====== NAVEGAÇÃO COM SETAS ======
            elif value == 1:  # Apenas quando pressionado
                if keycode in (ecodes.KEY_RIGHT, ecodes.KEY_UP):
                    logger.debug("Seta direita/cima → próxima cor")
                    mudar_cor(1)
                
                elif keycode in (ecodes.KEY_LEFT, ecodes.KEY_DOWN):
                    logger.debug("Seta esquerda/baixo → cor anterior")
                    mudar_cor(-1)
    
    except Exception as e:
        logger.error(f"Erro na thread teclado: {e}")

# ============================================================================
# THREAD 2: LISTENER CONSUMER CONTROL (event23)
# ============================================================================

def thread_consumer():
    """
    Monitora event23 (consumer control)
    - Vol+ → próxima cor (apenas em MODO LED)
    - Vol- → cor anterior (apenas em MODO LED)
    - Back → desativar MODO LED
    """
    global device_consumer
    
    if not device_consumer:
        logger.warning("Device consumer control não disponível!")
        return
    
    logger.info(f"🎛️  Listener Consumer Control iniciado: {device_consumer.name}")
    
    try:
        for event in device_consumer.read_loop():
            if event.type != ecodes.EV_KEY or event.value != 1:
                continue
            
            keycode = event.code
            
            # ====== MODO LED ATIVO ======
            if modo_led_ativo:
                if keycode == ecodes.KEY_VOLUMEUP:
                    logger.debug("Vol+ → próxima cor")
                    mudar_cor(1)
                
                elif keycode == ecodes.KEY_VOLUMEDOWN:
                    logger.debug("Vol- → cor anterior")
                    mudar_cor(-1)
                
                elif keycode == ecodes.KEY_BACK:
                    logger.info("Back → desativar MODO LED")
                    alternar_modo()
            
            # ====== FORA DO MODO LED ======
            else:
                # Vol+/Vol- passam para o sistema (ignoramos aqui)
                pass
    
    except Exception as e:
        logger.error(f"Erro na thread consumer: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("=" * 70)
    logger.info("🎨 CONTROLE DE LEDs - Air Mouse LE-7278 (v2)")
    logger.info("=" * 70)
    
    # Auto-detectar devices
    global device_teclado, device_consumer
    device_teclado, device_consumer = buscar_devices()
    
    if not device_teclado:
        logger.error("❌ Não foi possível iniciar: teclado não encontrado!")
        logger.error("\nDispositivos disponíveis:")
        for path in list_devices():
            try:
                dev = InputDevice(path)
                logger.error(f"  {path}: {dev.name}")
            except:
                pass
        sys.exit(1)
    
    logger.info("")
    logger.info("⚙️  Iniciando listeners...")
    logger.info("")
    logger.info("Comandos disponíveis:")
    logger.info("  • Long press OK (3s)      → Ativar/Desativar MODO LED")
    logger.info("  • Vol+ / Vol-             → Navegar cores (MODO LED ativo)")
    logger.info("  • Setas ← → ↑ ↓           → Navegar cores (qualquer hora)")
    logger.info("  • Back                    → Desativar MODO LED")
    logger.info("")
    logger.info("Log: %s", LOG_FILE)
    logger.info("Pressione Ctrl+C para sair")
    logger.info("")
    
    # Iniciar threads
    t1 = threading.Thread(target=thread_teclado, daemon=True, name="Teclado")
    t2 = threading.Thread(target=thread_consumer, daemon=True, name="Consumer")
    
    t1.start()
    if device_consumer:
        t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Encerrando daemon...")
        logger.info("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    main()
