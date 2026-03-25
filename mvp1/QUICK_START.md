# ⚡ Quick Start - Controle de LEDs com Air Mouse

**Tempo estimado: 10 minutos**

## 🎯 Objetivo

Usar o controle remoto Air Mouse LE-7278 para controlar as LEDs RGB do gabinete via long press OK + Vol+/Vol-.

## ✅ Checklist Pré-requisitos

- [ ] OpenRGB 0.9+ instalado e testado
- [ ] Placa-mãe com LEDs RGB (ASUS, MSI, Gigabyte, etc)
- [ ] Air Mouse LE-7278 com dongle USB
- [ ] Linux (Debian/Ubuntu)

---

## 🚀 Instalação (5 minutos)

### 1. Download dos arquivos

Você deve ter recebido:
- ✅ `controle_led.py` - Script principal
- ✅ `setup_controle_led.sh` - Instalador automático
- ✅ `teste_botoes.py` - Teste de botões
- ✅ `diagnostico_controle_led.sh` - Diagnóstico
- ✅ `air-mouse-leds.service` - Service file para autostart

**Copie para:**
```bash
~/Área de trabalho/PROJETOS/openrgb/
```

### 2. Execute o setup

```bash
cd ~/Área\ de\ trabalho/PROJETOS/openrgb

chmod +x setup_controle_led.sh
chmod +x diagnostico_controle_led.sh
chmod +x teste_botoes.py
chmod +x controle_led.py

./setup_controle_led.sh
```

### 3. Logout/Login

```bash
exit  # saia da sessão ou use: exec su - $USER
```

---

## 🧪 Teste Rápido (3 minutos)

### 1. Conecte o Air Mouse

- Conecte o dongle USB na porta USB do gabinete
- Aguarde 20-60 segundos
- Mova o mouse - deve aparecer cursor na tela

### 2. Diagnostic

```bash
~/Área\ de\ trabalho/PROJETOS/openrgb/diagnostico_controle_led.sh
```

Procure por:
- ✅ `python3-evdev`: OK
- ✅ `libnotify-bin`: OK
- ✅ Usuário no grupo `input`: OK
- ✅ Air Mouse detectado em `/dev/input/event*`
- ✅ OpenRGB funcionando

### 3. Teste dos botões

```bash
~/Área\ de\ trabalho/PROJETOS/openrgb/teste_botoes.py
```

Pressione:
- OK → deve aparecer `KEY_ENTER`
- Vol+ → deve aparecer `KEY_VOLUMEUP`
- Vol- → deve aparecer `KEY_VOLUMEDOWN`
- Back → deve aparecer `KEY_BACK`

---

## 🎮 Usar (2 minutos)

### Inicie o daemon

```bash
# Opção 1: Via alias (se setup funcionou)
led-daemon

# Opção 2: Via Python direto
python3 ~/Área\ de\ trabalho/PROJETOS/openrgb/controle_led.py
```

### Comandos

| Ação | Resultado |
|---|---|
| Long press **OK** (3s) | Ativa/Desativa MODO LED |
| **Vol+** (no modo LED) | Próxima cor |
| **Vol-** (no modo LED) | Cor anterior |
| **Back** (no modo LED) | Desativa modo |

### Cores disponíveis

1. 🔴 Vermelho
2. 🟠 Laranja
3. 🟡 Amarelo
4. 🟢 Verde
5. 🔵 Ciano
6. 🔷 Azul
7. 🟣 Roxo
8. 🟨 Ambar
9. ⚪ Branco
10. ⚫ Desligar

---

## 🔧 Troubleshooting Rápido

### "Device não encontrado"

```bash
# 1. Verificar USB
lsusb | grep -i 1915

# 2. Conectar Air Mouse novamente
# Aguarde 30 segundos

# 3. Testar novamente
python3 ~/Área\ de\ trabalho/PROJETOS/openrgb/teste_botoes.py
```

### "Permission denied"

```bash
# 1. Verificar grupo
groups $USER

# 2. Adicionar ao input se necessário
sudo usermod -aG input $USER
exit  # logout/login

# 3. Tentar novamente
```

### "LEDs não mudam"

```bash
# Testar OpenRGB manual
openrgb --device 0 --mode static --color FF0000
# Deve ficar vermelho

# Se não funcionar, tente com sudo
sudo openrgb --device 0 --mode static --color FF0000
```

### "Notificações não aparecem"

```bash
# Testar notify-send
notify-send "Teste" "Se viu isto, OK!" --icon=preferences-color

# Se não funcionar
sudo apt install libnotify-bin
```

---

## 📚 Próximos passos

### 1. Usar como autostart (opcional)

```bash
sudo cp ~/Área\ de\ trabalho/PROJETOS/openrgb/air-mouse-leds.service \
  /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable air-mouse-leds
sudo systemctl start air-mouse-leds
```

Verificar:
```bash
sudo systemctl status air-mouse-leds
```

### 2. Personalizar cores (opcional)

Edite `controle_led.py`:
```python
PALETA = [
    ("Meu Vermelho",   "FF0000"),
    ("Meu Azul",       "0000FF"),
    # ...adicione mais...
]
```

### 3. Mudar tempo de long press (opcional)

No `controle_led.py`:
```python
LONG_PRESS_TIME = 2.0  # mudou de 3.0 para 2.0 segundos
```

---

## 📝 Documentação Completa

Ver: `README_CONTROLE_LED.md`

---

## ❓ Dúvidas?

Consulte:
1. **Erros de instalação**: `diagnostico_controle_led.sh`
2. **Botões não funcionam**: `teste_botoes.py`
3. **Uso avançado**: `README_CONTROLE_LED.md`

---

**Status: ✅ Pronto para usar!**

Divirta-se controlando suas LEDs! 🎨✨
