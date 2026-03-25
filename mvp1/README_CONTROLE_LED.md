# 🎨 Controle de LEDs com Air Mouse LE-7278

Controle as LEDs RGB do seu gabinete usando o controle remoto Air Mouse **LELONG LE-7278** conectado via USB.

## ✨ Características

- ✅ **MODO LED inteligente**: Long press OK (3 segundos) ativa/desativa
- ✅ **Navegação cíclica**: Vol+/Vol- circulam entre 10 cores diferentes
- ✅ **Não interfere com volume**: LEDs só ativam quando modo está ON
- ✅ **Feedback visual**: Notificações desktop (notify-send)
- ✅ **Auto-detecção**: Procura os devices automaticamente
- ✅ **Sem sudo**: Configura grupo `input` para acesso direto

## 📋 Pré-requisitos

- Linux (Debian/Ubuntu)
- OpenRGB 0.9+ instalado e testado ✅
- Air Mouse LELONG LE-7278 com driver USB (ou Bluetooth)
- Python 3.6+
- Placa-mãe com controle de LEDs (ASUS, MSI, Gigabyte, etc)

## 🚀 Instalação Rápida

### 1️⃣ Clone ou copie os arquivos

```bash
cd ~/Área\ de\ trabalho/PROJETOS/openrgb
# Copie controle_led.py e setup_controle_led.sh para este diretório
```

### 2️⃣ Execute o setup

```bash
chmod +x setup_controle_led.sh
./setup_controle_led.sh
```

Isso vai:
- Instalar `python3-evdev` e `libnotify-bin`
- Adicionar seu usuário ao grupo `input` (requer logout/login)
- Criar aliases `led-daemon` e `led-stop`
- Gerar arquivo de serviço systemd (opcional)

### 3️⃣ Logout/Login

```bash
# Saia e entre novamente para aplicar mudanças do grupo input
exit
# ou
exec su - $USER
```

### 4️⃣ Conecte o Air Mouse

- Conecte o dongle USB na porta USB do gabinete
- Aguarde 20-60 segundos para o kernel carregar o driver
- Teste movimento do mouse na tela

### 5️⃣ Inicie o daemon

```bash
led-daemon
```

Você deve ver:

```
======================================================================
🎨 CONTROLE DE LEDs - Air Mouse LE-7278
======================================================================

🔍 Buscando devices do Air Mouse LE-7278...
  ✅ Teclado: /dev/input/event11 (XING WEI 2.4G USB USB Composite Device)
  ✅ Consumer: /dev/input/event23 (XING WEI 2.4G USB USB Composite Device Consumer Control)

⚙️  Iniciando listeners...

Comandos:
  • Long press OK (3s)  → Ativar/Desativar MODO LED
  • Vol+ / Vol-         → Navegar cores (quando MODO LED ativo)
  • Back                → Desativar MODO LED

Pressione Ctrl+C para sair
```

## 🎮 Como Usar

### ✨ Ativar MODO LED

1. Segure o botão **OK** do controle por **3 segundos**
2. Aparece notificação: `🎨 MODO LED - Ligado`
3. Agora Vol+/Vol- controlam as LEDs

### 🎨 Navegar entre cores

Com **MODO LED ativo**, pressione:

- **Vol+** → Próxima cor (avança na paleta cíclica)
- **Vol-** → Cor anterior (recua)

Cores disponíveis (em ordem):
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

Cada mudança mostra uma notificação breve com o nome da cor.

### 🔕 Desativar MODO LED

Escolha uma opção:

1. Segure **OK** novamente por 3 segundos (como um toggle)
2. Pressione **Back** para sair imediatamente

Quando desativado, Vol+/Vol- voltam ao comportamento normal do sistema.

## 🖥️ Instalação como Serviço (Autostart)

Para que o daemon inicie automaticamente com o desktop:

```bash
# Copiar service file para systemd
sudo cp /tmp/air-mouse-leds.service /etc/systemd/system/

# Recarregar configuração
sudo systemctl daemon-reload

# Habilitar autostart
sudo systemctl enable air-mouse-leds

# Iniciar agora
sudo systemctl start air-mouse-leds

# Verificar status
sudo systemctl status air-mouse-leds
```

### Comandos do systemd

```bash
# Ver logs em tempo real
sudo journalctl -u air-mouse-leds -f

# Parar o serviço
sudo systemctl stop air-mouse-leds

# Desabilitar autostart
sudo systemctl disable air-mouse-leds

# Reiniciar
sudo systemctl restart air-mouse-leds
```

## 🔧 Troubleshooting

### "Device não encontrado"

Se aparecer `❌ Não consegui encontrar os devices!`:

1. **Verifique conexão USB**:
   ```bash
   lsusb | grep -i "xing\|lelong\|1915"
   ```
   Deve aparecer algo como: `Bus 001 Device 005: ID 1915:1025 ...`

2. **Liste todos os input devices**:
   ```bash
   ls -la /dev/input/event*
   sudo evtest
   # Procure por "XING WEI" na lista
   ```

3. **Teste com evtest**:
   ```bash
   sudo evtest /dev/input/event11
   # Pressione botões e veja os eventos
   ```

### "Permission denied"

Se aparecer erro de permissão ao acessar /dev/input/:

1. Verifique se está no grupo `input`:
   ```bash
   groups $USER
   # Deve aparecer "input" na lista
   ```

2. Se não aparecer, adicione novamente:
   ```bash
   sudo usermod -aG input $USER
   exit  # logout/login necessário
   ```

### Notificações não aparecem

Teste notify-send manualmente:

```bash
notify-send "Teste" "Se você viu isso, está funcionando!" --icon=preferences-color
```

Se não funcionar:
- Verifique se `libnotify-bin` está instalado: `sudo apt install libnotify-bin`
- Se usar GNOME/KDE, notificações devem estar habilitadas

### LEDs não mudam de cor

1. Verifique se OpenRGB está funcionando:
   ```bash
   openrgb --version
   openrgb --list-devices
   ```

2. Teste manualmente:
   ```bash
   openrgb --device 0 --mode static --color FF0000  # Vermelho
   openrgb --device 0 --mode static --color 0000FF  # Azul
   ```

3. Se precisar de `sudo`:
   ```bash
   sudo openrgb --device 0 --mode static --color FF0000
   ```
   Neste caso, o script já tenta com sudo automaticamente.

## 📝 Personalização

### Mudar a paleta de cores

Edite `controle_led.py` e procure por:

```python
PALETA = [
    ("Vermelho",   "FF0000"),
    ("Laranja",    "FF5500"),
    ...
]
```

Adicione/remova cores conforme desejar. Cores no formato HEX (RRGGBB).

### Mudar tempo de long press

Procure por:

```python
LONG_PRESS_TIME = 3.0  # segundos
```

Altere para seu valor preferido (ex: 2.0 para 2 segundos).

### Mudar device a monitorar

O script auto-detecta automaticamente, mas se quiser forçar:

```python
# No final da função main():
DEVICE_TECLADO = InputDevice('/dev/input/event11')  # Ajuste conforme necessário
DEVICE_CONSUMER = InputDevice('/dev/input/event23')
```

## 🐛 Debug

Para ver mensagens detalhadas:

```bash
# Edite controle_led.py e remova os comentários de:
# print("  [OK] pressionado...")
# print("  [OK] press curto...")

# Ou execute com Python diretamente:
python3 -u ~/Área\ de\ trabalho/PROJETOS/openrgb/controle_led.py
```

## 📦 Dependências Instaladas

| Pacote | Versão | Uso |
|---|---|---|
| python3-evdev | 1.4+ | Captura de eventos de input |
| libnotify-bin | 0.7+ | Notificações desktop |
| openrgb | 0.9+ | Controle de LEDs |

## 🔒 Segurança & Permissões

- ✅ Não usa `sudo` em execução normal (apenas grupo `input`)
- ✅ Apenas daemon systemd usa `sudo` (necessário para algunos drivers)
- ✅ Arquivo de configuração local, sem instalação global
- ✅ Pode ser desabilitado a qualquer momento

## 📄 Licença

Livre para uso pessoal e modificação.

## 🤝 Contribuições

Encontrou um bug ou quer melhorar? Abra uma issue ou pull request!

---

**Aproveite controlando suas LEDs! 🎨✨**
