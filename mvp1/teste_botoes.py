#!/usr/bin/env python3
"""
🧪 Teste Manual - Veja eventos dos botões do Air Mouse em tempo real

Útil para:
- Descobrir qual /dev/input/event* é o seu controle
- Ver quais keycodes cada botão gera
- Debugar problemas de reconhecimento
"""

import sys
from evdev import InputDevice, ecodes, list_devices
from pathlib import Path

def list_air_mouse_devices():
    """Lista todos os Air Mouse conectados"""
    print("=" * 70)
    print("🔍 Procurando Air Mouse LE-7278 conectados...")
    print("=" * 70)
    print()
    
    devices = list_devices()
    encontrados = []
    
    for device_path in devices:
        try:
            device = InputDevice(device_path)
            nome = device.name.lower()
            
            if "xing wei" in nome or "lelong" in nome or "2.4g" in nome:
                encontrados.append((device_path, device.name, device.phys))
                tipo = "❓ Desconhecido"
                if "consumer" in nome:
                    tipo = "🎛️  Consumer Control (Vol, Menu, etc)"
                elif "system" in nome:
                    tipo = "⚡ System Control (Power, Sleep)"
                else:
                    tipo = "🎹 Teclado Principal (Setas, OK, etc)"
                
                print(f"  {device_path}")
                print(f"    Nome: {device.name}")
                print(f"    Tipo: {tipo}")
                print(f"    Phys: {device.phys}")
                print()
        except Exception as e:
            pass
    
    if not encontrados:
        print("  ❌ Nenhum Air Mouse encontrado!")
        print()
        print("  Possíveis causas:")
        print("    1. O controle não está conectado")
        print("    2. O driver USB não foi carregado")
        print("    3. O controle está em Bluetooth (desconectar e reconectar na USB)")
        print()
        return None
    
    return encontrados

def test_device(device_path):
    """Testa um device específico"""
    print()
    print("=" * 70)
    print(f"🧪 Testando: {device_path}")
    print("=" * 70)
    print()
    
    try:
        device = InputDevice(device_path)
        print(f"Device: {device.name}")
        print(f"FD: {device.fd}")
        print()
        print("Pressione botões no controle remoto...")
        print("(Pressione Ctrl+C para parar)")
        print()
        
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                try:
                    key_name = ecodes.KEY[event.code]
                except KeyError:
                    key_name = f"UNKNOWN({event.code})"
                
                estado = {
                    0: "RELEASED ⬆️",
                    1: "PRESSED  ⬇️",
                    2: "REPEAT   🔁"
                }
                
                estado_str = estado.get(event.value, f"UNKNOWN({event.value})")
                
                print(f"  🔘 {key_name:20} {estado_str}")
    
    except KeyError:
        print(f"❌ Device {device_path} não encontrado!")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido")

def interactive_mode():
    """Modo interativo para escolher device"""
    encontrados = list_air_mouse_devices()
    
    if not encontrados:
        print("\nTente:")
        print("  1. Conectar o controle na USB")
        print("  2. Aguardar 20-60 segundos")
        print("  3. Rodar este script novamente")
        return
    
    if len(encontrados) == 1:
        print("Apenas um device encontrado. Testando automaticamente...")
        test_device(encontrados[0][0])
    else:
        print("Qual device você quer testar?")
        print()
        for i, (path, name, phys) in enumerate(encontrados, 1):
            print(f"  {i}. {path} - {name}")
        print()
        
        choice = input("Digite o número (ou Enter para o primeiro): ").strip()
        
        try:
            idx = int(choice) - 1 if choice else 0
            if 0 <= idx < len(encontrados):
                test_device(encontrados[idx][0])
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")

def manual_mode(device_path):
    """Teste um device específico passado via argumentos"""
    print()
    print("=" * 70)
    print(f"🧪 Testando Device Manual: {device_path}")
    print("=" * 70)
    print()
    
    try:
        device = InputDevice(device_path)
        print(f"✅ Conectado: {device.name}")
        print()
        print("Pressione botões (Ctrl+C para parar)...")
        print()
        
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                try:
                    key_name = ecodes.KEY[event.code]
                except KeyError:
                    key_name = f"CODE_{event.code}"
                
                estados = ["RELEASE", "PRESS", "REPEAT"]
                estado = estados[event.value] if event.value < 3 else f"VALUE_{event.value}"
                
                print(f"  {key_name:25} {estado:10} (code={event.code:3d})")
    
    except (KeyError, FileNotFoundError):
        print(f"❌ Device não encontrado: {device_path}")
        print()
        print("Dispositivos disponíveis:")
        for dev_path in list_devices():
            try:
                dev = InputDevice(dev_path)
                print(f"  {dev_path}: {dev.name}")
            except:
                pass
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste finalizado")

def main():
    if len(sys.argv) > 1:
        # Modo manual: python3 teste_botoes.py /dev/input/event11
        manual_mode(sys.argv[1])
    else:
        # Modo interativo
        interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
