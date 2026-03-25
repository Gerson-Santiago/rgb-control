#!/usr/bin/env python3
"""
teste_ok.py — detecta em qual device o botão OK está sendo recebido
Rodar: sudo python3 teste_ok.py
"""

import time
import sys
import threading
from evdev import InputDevice, list_devices  # type: ignore[import]

def encontrar_todos_xingwei():
    """Retorna TODOS os devices que batem com o Air Mouse."""
    encontrados = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if any(x in dev.name.lower() for x in ("xing wei", "lelong", "2.4g")):
                encontrados.append(dev)
                print(f"  📌 {path}  →  {dev.name}", flush=True)
        except Exception:
            pass
    return encontrados

def monitorar(dev):
    """Thread: imprime todos os eventos de um device."""
    try:
        for ev in dev.read_loop():
            if ev.type == 0:    # EV_SYN — muito verboso, filtra
                continue
            print(f"  [{dev.path}]  type={ev.type}  code={ev.code}  value={ev.value}", flush=True)
    except Exception as e:
        print(f"  ❌ Erro em {dev.path}: {e}", flush=True)

def main():
    print("🔍 Listando todos os devices XING WEI / Air Mouse...\n", flush=True)
    devices = encontrar_todos_xingwei()

    if not devices:
        print("❌ Nenhum device encontrado. Conecte o dongle USB.")
        sys.exit(1)

    print(f"\n✅ {len(devices)} device(s) encontrado(s)")
    print("🔬 Monitorando TODOS em paralelo — pressione botões do controle!")
    print("   Ctrl+C para sair\n", flush=True)

    threads = []
    for dev in devices:
        t = threading.Thread(target=monitorar, args=(dev,), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Teste encerrado.")
        print("\n💡 O device que mostrou eventos ao pressionar OK é o teclado principal.")

if __name__ == "__main__":
    main()
