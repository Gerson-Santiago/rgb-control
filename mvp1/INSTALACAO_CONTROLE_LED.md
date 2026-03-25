# 🎮 Instalação e Teste do Controle de LEDs

## 📋 Pré-requisitos

### 1️⃣ Instalar dependências
```bash
# Biblioteca evdev para capturar eventos de input
sudo apt install python3-evdev

# Ferramenta de notificação desktop (provavelmente já tem)
sudo apt install libnotify-bin

# OpenRGB já deve estar instalado ✅
which openrgb
```

### 2️⃣ Adicionar usuário ao grupo `input`
Para **não precisar de sudo** ao executar:

```bash
sudo usermod -aG input $USER

# Fazer efeito imediatamente (ou fazer logout/login):
newgrp input
```

**Verificar:**
```bash
groups $USER
# Deve conter "input"
```

---

## 🚀 Teste Rápido (sem instalar)

### Opção A: Versão Original (v1 - Simples)
```bash
# Ir ao diretório do projeto
cd ~/Área\ de\ trabalho/PROJETOS/openrgb

# Executar (com Ctrl+C para parar)
python3 controle_led.py
```

### Opção B: Versão Melhorada (v2 - Com logging)
```bash
# Copiar arquivo
cp ~/controle_led_v2.py ~/Área\ de\ trabalho/PROJETOS/openrgb/

# Executar
python3 ~/Área\ de\ trabalho/PROJETOS/openrgb/controle_led_v2.py
```

**Diferenças v1 vs v2:**

| Recurso | v1 | v2 |
|---|---|---|
| Long press OK | ✅ | ✅ |
| Vol+/Vol- navegação | ✅ | ✅ |
| **Setas ↑↓←→** | ❌ | ✅ |
| Logging em arquivo | ❌ | ✅ |
| Detecção de erros | Simples | Robusta |
| Código limpo | ✅ | ✅ |

**Recomendação:** Use v2 para ter suporte a setas conforme seu plano!

---

## 🧪 Testes Manuais

### Teste 1: Auto-detecção de devices
```bash
python3 controle_led_v2.py
```

**Esperado na saída:**
```
✅ Teclado encontrado: /dev/input/event11 - XING WEI 2.4G USB ...
✅ Consumer Control encontrado: /dev/input/event23 - XING WEI 2.4G ...
```

Se não aparecer, verifique:
```bash
# Ver todos os devices
sudo evtest | grep XING
```

### Teste 2: Long press OK (3s)
1. Execute o script
2. Segure o botão OK por **exatamente 3+ segundos**
3. **Esperado:** Notificação "🎨 MODO LED Ligado"
4. Solte e segure novamente por 3s
5. **Esperado:** Notificação "🔕 MODO LED Desligado"

### Teste 3: Navegação com Setas (MODO LED Ligado)
1. Ative MODO LED (long press OK)
2. Pressione **seta direita →**
3. **Esperado:** LED muda para próxima cor
4. Pressione **seta esquerda ←**
5. **Esperado:** LED volta para cor anterior

### Teste 4: Navegação com Vol+/Vol- (MODO LED Ligado)
1. Ative MODO LED
2. Pressione **Vol+**
3. **Esperado:** Próxima cor
4. Pressione **Vol-**
5. **Esperado:** Cor anterior

### Teste 5: Back desativa MODO LED
1. Ative MODO LED
2. Pressione **Back**
3. **Esperado:** MODO LED desativa imediatamente (sem esperar 3s)

### Teste 6: Notificações
1. Todas as ações devem gerar notificações no desktop
2. Ver arquivo de log:
```bash
cat ~/.cache/controle_led/controle_led.log
tail -f ~/.cache/controle_led/controle_led.log  # Acompanhar em tempo real
```

---

## 📦 Instalação Permanente (Systemd Service)

### Passo 1: Copiar script para local apropriado
```bash
sudo cp ~/controle_led_v2.py /usr/local/bin/controle_led
sudo chmod +x /usr/local/bin/controle_led
```

### Passo 2: Criar arquivo de serviço
```bash
sudo nano /etc/systemd/system/controle_led.service
```

**Conteúdo:**
```ini
[Unit]
Description=Control LEDs with Air Mouse LE-7278
After=network.target

[Service]
Type=simple
User=sant
ExecStart=/usr/bin/python3 /usr/local/bin/controle_led
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Passo 3: Habilitar e iniciar
```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar para autostart
sudo systemctl enable controle_led.service

# Iniciar agora
sudo systemctl start controle_led.service

# Ver status
sudo systemctl status controle_led.service

# Ver logs
sudo journalctl -u controle_led -f
```

### Passo 4: Parar/Reiniciar quando precisar
```bash
# Parar
sudo systemctl stop controle_led

# Reiniciar
sudo systemctl restart controle_led

# Desabilitar autostart
sudo systemctl disable controle_led
```

---

## 🔧 Troubleshooting

### ❌ "evdev not found"
```bash
pip install evdev
# ou
sudo apt install python3-evdev
```

### ❌ "Device not found"
```bash
# Ver todos os devices
ls -la /dev/input/event*

# Testar com evtest
sudo evtest
# (selecione o device XING WEI)
```

### ❌ "Permission denied" ao aplicar cor
```bash
# Adicione ao grupo input
sudo usermod -aG input $USER
newgrp input

# Ou execute com sudo
sudo /usr/local/bin/controle_led
```

### ❌ "notify-send: not found"
```bash
sudo apt install libnotify-bin
# ou para GNOME
sudo apt install gnome-shell-notifications
```

### ⚠️ Setas não funcionam
```bash
# Verificar se estão em event11
sudo evtest /dev/input/event11
# (Pressione setas e veja se aparecem KEY_UP, KEY_DOWN, etc)
```

---

## 📝 Criando um Alias

Para executar facilmente de qualquer lugar:

```bash
# Editar ~/.bashrc
nano ~/.bashrc

# Adicionar no final:
alias led-ctrl='python3 ~/Área\ de\ trabalho/PROJETOS/openrgb/controle_led_v2.py'

# Atualizar bash
source ~/.bashrc

# Usar:
led-ctrl
```

---

## 📊 Estrutura Final de Arquivos

```
~/Área de trabalho/PROJETOS/openrgb/
├── rbg.sh                      (existente)
├── config.txt                  (existente)
├── controle_led.py             (v1 - simples)
├── controle_led_v2.py          (v2 - recomendado)
├── relatorio_diagnostico.md    (existente)
└── log*.md                      (existente)

~/.cache/controle_led/
└── controle_led.log            (criado automaticamente)
```

---

## ✅ Checklist Final

- [ ] Python3 e evdev instalados
- [ ] Usuário no grupo `input`
- [ ] Script executável
- [ ] Teste rápido funcionando
- [ ] Notificações aparecendo
- [ ] Log sendo criado
- [ ] (Opcional) Systemd service instalado
- [ ] (Opcional) Alias criado

---

## 🎯 Próximas Etapas

1. **Teste v2**: Execute e confirme que tudo funciona
2. **Feedback**: Qualquer problema? Compartilhe os logs!
3. **Customização**: Quer mudar cores, botões ou comportamento?
4. **Integração**: Quando tudo estiver ok, instalamos como serviço permanente

---

**Dúvidas? Use:**
```bash
# Ver ajuda do script
python3 controle_led_v2.py --help  # (se implementado)

# Ver logs em tempo real
tail -f ~/.cache/controle_led/controle_led.log
```
