# 🎮 Plano: Controlar LEDs com Air Mouse LE-7278

## 📋 OBJETIVO FINAL
Usar os botões do controle remoto **LELONG LE-7278** para controlar as LEDs RGB do gabinete através do script `rbg.sh` e/ou Python.

---

## 🔍 FASE 1: DIAGNÓSTICO & SETUP

### 1.1 Conectar o Controle
- [ ] Conectar controle via **USB** (recomendado inicialmente)
- [ ] Aguardar 20-60 segundos para instalação do driver
- [ ] Testar movimento do cursor/mouse

### 1.2 Identificar o Device no Linux
Quando conectado, o controle aparecerá como um novo `/dev/input/event*`

**Comando para verificar:**
```bash
sudo evtest
# ou
lsusb | grep -i "lelong\|xing\|1915"  # ID do fabricante
ls -la /dev/input/event*
```

### 1.3 Mapear os Botões
- [ ] Usar `evtest` para ver qual evento cada botão gera
- [ ] Documentar os key codes (ex: KEY_UP, KEY_PLAY, etc)
- [ ] Criar tabela de mapeamento botão → ação LED

---

## 🎯 FASE 2: ARQUITETURA DA SOLUÇÃO

### Opção A: Script Bash + Listener Python (RECOMENDADO)
```
┌─────────────────────┐
│  Air Mouse LE-7278  │
│  (USB/Bluetooth)    │
└──────────┬──────────┘
           │ /dev/input/eventX
           ▼
┌─────────────────────────────┐
│  python-listener.py         │
│  (Captura eventos evdev)    │
└──────────┬──────────────────┘
           │ Detecção de botão
           ▼
┌─────────────────────────────┐
│  rbg.sh + cores             │
│  (Executa comando da cor)   │
└──────────┬──────────────────┘
           │ Via subprocess
           ▼
┌─────────────────────────────┐
│  OpenRGB                    │
│  (Aplica cor aos LEDs)      │
└─────────────────────────────┘
```

### Opção B: Remapeamento Udev + Systemd Service
- Mapear botões via udev rules
- Executar ações via systemd socket
- Mais complexo, mas mais integrado

### Opção C: Keybinding via Sistema X11/Wayland
- Mapear botões como atalhos do sistema
- Limita a controle local

**→ Vamos com a Opção A primeiro!**

---

## 🛠️ FASE 3: IMPLEMENTAÇÃO

### 3.1 Dependências Python
```bash
pip install evdev  # Para capturar eventos de input
```

### 3.2 Script Python: `air_mouse_listener.py`
```python
#!/usr/bin/env python3
import subprocess
from evdev import InputDevice, categorize, ecodes
import sys

# Configuração
DEVICE_PATH = "/dev/input/eventX"  # SERÁ DESCOBERTO
COLOR_MAPPINGS = {
    # key_code: comando rbg
    "KEY_VOLUMEUP": "rbg red",
    "KEY_VOLUMEDOWN": "rbg blue",
    "KEY_PLAYPAUSE": "rbg green",
    "KEY_UP": "rbg yellow",
    "KEY_DOWN": "rbg off",
    # ... adicionar mais conforme necessário
}

def execute_rbg(command):
    """Executa comando rbg.sh"""
    try:
        subprocess.run(command.split(), check=True)
        print(f"✅ Executado: {command}")
    except Exception as e:
        print(f"❌ Erro: {e}")

def listen_to_device(device_path):
    """Escuta eventos do controle remoto"""
    try:
        device = InputDevice(device_path)
        print(f"🎮 Escutando: {device.name}")
        print("Pressione botões no controle remoto...\n")
        
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                key_name = key_event.keycode
                
                if key_event.keystate == 1:  # 1 = pressed, 0 = released
                    print(f"🔘 Botão pressionado: {key_name}")
                    
                    if key_name in COLOR_MAPPINGS:
                        command = COLOR_MAPPINGS[key_name]
                        execute_rbg(command)
                    else:
                        print(f"   (sem ação mapeada)")
    
    except KeyError:
        print(f"❌ Device {device_path} não encontrado")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Listener encerrado")

if __name__ == "__main__":
    device = sys.argv[1] if len(sys.argv) > 1 else DEVICE_PATH
    listen_to_device(device)
```

### 3.3 Script de Descoberta: `find_air_mouse.sh`
```bash
#!/bin/bash
echo "🔍 Procurando controle remoto air mouse..."
echo ""

# Método 1: Via lsusb
echo "📱 Dispositivos USB detectados:"
lsusb | grep -i "lelong\|1915\|2.4g"

echo ""
echo "📡 Dispositivos /dev/input/event:"
for event in /dev/input/event*; do
    sudo evtest --query "$event" NAME 2>/dev/null | grep -q "XING\|Lelong\|2.4G" && {
        echo "✅ Encontrado: $event - $(sudo cat /proc/bus/input/devices | grep -A1 "$event" | tail -1)"
    }
done

echo ""
echo "💡 Use: sudo evtest /dev/input/eventX para testar"
```

---

## 📊 FASE 4: MAPEAMENTO DE BOTÕES

Baseado no manual LE-7278, botões disponíveis:
- ✅ Volume +/- (KEY_VOLUMEUP, KEY_VOLUMEDOWN)
- ✅ Play/Pause (KEY_PLAYPAUSE)
- ✅ Setas directas (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT)
- ✅ OK/Enter (KEY_ENTER)
- ✅ Home/Back (KEY_HOME, KEY_BACK)
- ✅ Menu (KEY_MENU)
- ✅ Muitos outros...

**Sugestão de mapeamento LED:**
```
Volume +     → Aumentar brilho / Próxima cor
Volume -     → Diminuir brilho / Cor anterior
Play/Pause   → Ciclo de cores
Setas        → Mudar cor (↑ branco, ↓ preto, ← vermelho, → azul)
OK           → Aplicar cor customizada
Home         → Restaurar cor padrão
Menu         → Mostrar status atual
```

---

## ⚙️ FASE 5: INTEGRAÇÃO COM SISTEMA

### 5.1 Criar Systemd Service
```ini
# /etc/systemd/system/air-mouse-leds.service
[Unit]
Description=Control LEDs with Air Mouse
After=network.target

[Service]
Type=simple
User=sant
ExecStart=/usr/local/bin/air_mouse_listener.py /dev/input/eventX
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Executar como Daemon
```bash
sudo systemctl enable air-mouse-leds
sudo systemctl start air-mouse-leds
sudo systemctl status air-mouse-leds
```

---

## 🧪 FASE 6: TESTES

1. [ ] Listener rodando e escutando corretamente
2. [ ] Botão pressionado → mensagem no console
3. [ ] Botão mapeado → comando rbg executado
4. [ ] LEDs mudam de cor
5. [ ] Sem lag entre pressão e resposta
6. [ ] Systemd service funcionando automaticamente

---

## 📝 PRÓXIMOS PASSOS

1. **Conectar o controle** na USB
2. **Identificar** qual /dev/input/event* é
3. **Testar com evtest** qual tecla é qual evento
4. **Criar mapeamento** personalizado
5. **Adaptar script Python** com suas preferências
6. **Testar localmente**
7. **Integrar como serviço**

---

## 💾 ESTRUTURA DE ARQUIVOS FINAL

```
/home/sant/Área de trabalho/PROJETOS/openrgb/
├── rbg.sh                          (existente ✅)
├── config.txt                      (existente ✅)
├── air_mouse_listener.py           (NOVO)
├── find_air_mouse.sh               (NOVO)
├── air_mouse_mappings.json         (NOVO - opcional)
└── systemd/
    └── air-mouse-leds.service      (NOVO - opcional)
```

---

**Status: 📋 PRONTO PARA INICIAR FASE 1**

Próxima ação: Conectar o controle e descobrir seu /dev/input/event*
