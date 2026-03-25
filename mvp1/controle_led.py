#!/usr/bin/env python3
"""
🎨 Controlar LEDs do gabinete com Air Mouse LE-7278
Usa MODO LED: Long press OK (3s) ativa/desativa
Vol+/Vol- navegam entre cores (apenas no MODO LED)
Back desativa o modo
"""

import threading
import time
import subprocess
import sys
from evdev import InputDevice, ecodes, list_devices
from pathlib import Path

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

# Tempo para long press (segundos)
LONG_PRESS_TIME = 3.0

# Device IDs (vão ser auto-detectados)
DEVICE_TECLADO = None      # event11 (XING WEI ... Composite Device)
DEVICE_CONSUMER = None     # event23 (XING WEI ... Consumer Control)

# Estado global
modo_led_ativo = False
indice_cor = 8  # Começa com Branco
lock = threading.Lock()

# Para detectar long press
ok_press_time = None

# ============================================================================
# FUNÇÕES DE DEVICE
# ============================================================================

def buscar_devices():
    """Auto-detecta os devices pelo nome do fabricante"""
    global DEVICE_TECLADO, DEVICE_CONSUMER
    
    print("🔍 Buscando devices do Air Mouse LE-7278...")
    
    devices = list_devices()
    encontrados = {}
    
    for device_path in devices:
        try:
            device = InputDevice(device_path)
            nome = device.name.lower()
            
            # Procura por "XING WEI" ou "Lelong" no nome
            if "xing wei" in nome or "lelong" in nome or "2.4g" in nome:
                # Diferencia pelo tipo
                if "consumer" in nome or "consumer control" in nome:
                    encontrados['consumer'] = (device_path, device.name)
                elif "system" in nome or "system control" in nome:
                    encontrados['system'] = (device_path, device.name)
                else:
                    # Assume que é o teclado principal
                    encontrados['teclado'] = (device_path, device.name)
        except Exception as e:
            pass
    
    # Atribui os devices encontrados
    if 'teclado' in encontrados:
        DEVICE_TECLADO = InputDevice(encontrados['teclado'][0])
        print(f"  ✅ Teclado: {encontrados['teclado'][0]} ({encontrados['teclado'][1]})")
    else:
        print("  ❌ Teclado não encontrado!")
    
    if 'consumer' in encontrados:
        DEVICE_CONSUMER = InputDevice(encontrados['consumer'][0])
        print(f"  ✅ Consumer: {encontrados['consumer'][0]} ({encontrados['consumer'][1]})")
    else:
        print("  ❌ Consumer Control não encontrado!")
    
    if not DEVICE_TECLADO or not DEVICE_CONSUMER:
        print("\n❌ Não consegui encontrar os devices!")
        print("   Conecte o Air Mouse LE-7278 e tente novamente.")
        return False
    
    return True

# ============================================================================
# NOTIFICAÇÕES
# ============================================================================

def notificar(titulo, mensagem, urgencia="normal", tempo=3000):
    """Envia notificação desktop com notify-send"""
    try:
        subprocess.run([
            "notify-send",
            titulo,
            mensagem,
            f"--urgency={urgencia}",
            f"--expire-time={tempo}",
            "--icon=preferences-color"
        ], check=False)
    except Exception as e:
        print(f"⚠️  Erro na notificação: {e}")

# ============================================================================
# CONTROLE DE LEDs
# ============================================================================

def aplicar_cor(hex_color, nome_cor):
    """Aplica cor aos LEDs usando openrgb"""
    try:
        # Remove # se existir
        hex_color = hex_color.lstrip('#')
        
        cmd = [
            "openrgb",
            "--device", "0",
            "--mode", "static",
            "--color", hex_color
        ]
        
        # Tenta com sudo se falhar sem
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=5)
        except subprocess.CalledProcessError:
            cmd_sudo = ["sudo"] + cmd
            subprocess.run(cmd_sudo, check=True, capture_output=True, timeout=5)
        
        print(f"  🎨 Cor aplicada: {nome_cor}")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao aplicar cor: {e}")
        return False

def mudar_cor(delta):
    """Navega na paleta: delta=1 (próxima), delta=-1 (anterior)"""
    global indice_cor
    
    with lock:
        # Navegação cíclica
        indice_cor = (indice_cor + delta) % len(PALETA)
        nome, cor = PALETA[indice_cor]
        
        # Aplica ao sistema
        if aplicar_cor(cor, nome):
            # Notificação breve
            notificar("🎨 Cor", nome, "low", 1500)

def alternar_modo():
    """Liga/desliga MODO LED"""
    global modo_led_ativo
    
    with lock:
        modo_led_ativo = not modo_led_ativo
        
        if modo_led_ativo:
            notificar(
                "🎨 MODO LED",
                "Ligado — use Vol+/Vol- para mudar as cores",
                "normal",
                3000
            )
            print("✅ MODO LED: LIGADO")
        else:
            notificar(
                "🔕 MODO LED",
                "Desligado",
                "low",
                2000
            )
            print("❌ MODO LED: DESLIGADO")

# ============================================================================
# THREAD 1: Monitorar Teclado (OK com long press)
# ============================================================================

def thread_teclado():
    """Escuta event11 (teclado) para detectar long press do OK"""
    global ok_press_time
    
    print("🎹 Thread Teclado iniciada")
    
    if not DEVICE_TECLADO:
        print("❌ Device Teclado não disponível!")
        return
    
    for event in DEVICE_TECLADO.read_loop():
        try:
            # Detecta KEY_ENTER (botão OK)
            if event.type == ecodes.EV_KEY and event.code == ecodes.KEY_ENTER:
                
                if event.value == 1:  # Pressionado
                    ok_press_time = time.time()
                    # print("  [OK] pressionado...")
                
                elif event.value == 0:  # Solto
                    if ok_press_time:
                        duracao = time.time() - ok_press_time
                        ok_press_time = None
                        
                        if duracao >= LONG_PRESS_TIME:
                            print(f"  [OK] long press detectado ({duracao:.1f}s)")
                            alternar_modo()
                        # else:
                        #     print(f"  [OK] press curto ({duracao:.1f}s) - ignorado")
        
        except Exception as e:
            print(f"❌ Erro na thread teclado: {e}")

# ============================================================================
# THREAD 2: Monitorar Consumer Control (Vol+, Vol-, Back)
# ============================================================================

def thread_consumer():
    """Escuta event23 (consumer control) para Vol+, Vol-, Back"""
    
    print("🎛️  Thread Consumer Control iniciada")
    
    if not DEVICE_CONSUMER:
        print("❌ Device Consumer Control não disponível!")
        return
    
    for event in DEVICE_CONSUMER.read_loop():
        try:
            if event.type == ecodes.EV_KEY and event.value == 1:  # Pressionado
                
                if event.code == ecodes.KEY_VOLUMEUP:
                    if modo_led_ativo:
                        print("  [Vol+] navegar cor (próxima)")
                        mudar_cor(1)
                    else:
                        pass  # Vol+ normal, ignoramos aqui
                
                elif event.code == ecodes.KEY_VOLUMEDOWN:
                    if modo_led_ativo:
                        print("  [Vol-] navegar cor (anterior)")
                        mudar_cor(-1)
                    else:
                        pass  # Vol- normal, ignoramos aqui
                
                elif event.code == ecodes.KEY_BACK:
                    if modo_led_ativo:
                        print("  [Back] desativar MODO LED")
                        alternar_modo()
                    # else: Back ignorado fora do modo
        
        except Exception as e:
            print(f"❌ Erro na thread consumer: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("🎨 CONTROLE DE LEDs - Air Mouse LE-7278")
    print("=" * 70)
    print()
    
    # Busca devices
    if not buscar_devices():
        sys.exit(1)
    
    print()
    print("⚙️  Iniciando listeners...")
    print()
    print("Comandos:")
    print("  • Long press OK (3s)  → Ativar/Desativar MODO LED")
    print("  • Vol+ / Vol-         → Navegar cores (quando MODO LED ativo)")
    print("  • Back                → Desativar MODO LED")
    print()
    print("Pressione Ctrl+C para sair")
    print()
    
    # Threads
    t1 = threading.Thread(target=thread_teclado, daemon=True)
    t2 = threading.Thread(target=thread_consumer, daemon=True)
    
    t1.start()
    t2.start()
    
    try:
        # Mantém o programa rodando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Encerrando daemon...")
        sys.exit(0)

if __name__ == "__main__":
    main()
