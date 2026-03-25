# 🎮 Quick Reference - Controle de LEDs

## ⚡ Comandos Mais Usados

```bash
# Executar o script
python3 ~/controle_led_v2.py

# Ver logs em tempo real
tail -f ~/.cache/controle_led/controle_led.log

# Testar device teclado
sudo evtest /dev/input/event11

# Testar device consumer
sudo evtest /dev/input/event23

# Ver todos os devices
lsusb | grep -i "xing\|lelong\|1915"

# Parar o systemd service
sudo systemctl stop controle_led

# Ver status
sudo systemctl status controle_led
```

---

## 🎮 Botões do Controle

### Ativar/Desativar MODO LED
```
┌─────────────────────┐
│  Segure OK por 3s   │
│  (Notificação aparece)
└─────────────────────┘
```

### Navegar Cores (quando MODO LED ativo)
```
┌────────────────────┐
│  Vol+ / Vol-       │  → Próxima / Anterior
│  ou                │
│  Seta → / ← ou ↑↓  │  → Próxima / Anterior
└────────────────────┘
```

### Desativar Rapidamente
```
┌─────────────────────┐
│  Back               │  → Sai do MODO LED
└─────────────────────┘
```

---

## 📝 Paleta de Cores Padrão

```
0. Vermelho        #FF0000
1. Laranja         #FF5500
2. Amarelo         #FFFF00
3. Verde           #00FF00
4. Ciano           #00F2EA
5. Azul            #0000FF
6. Roxo            #AA00FF
7. Ambar           #FFB200
8. Branco          #FFFFFF
9. Desligar        #000000
```

---

## 🔧 Edição Rápida

### Mudar cores
```python
PALETA = [
    ("Vermelho",   "FF0000"),
    ("Pink",       "FF10F0"),  # ← Adicione aqui
]
```

### Mudar duração long press
```python
LONG_PRESS_TIME = 2.0  # De 3s para 2s
```

### Desabilitar notificações
```python
# notificar("🎨 Cor", nome, "low", 1500)  # Comente
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|---|---|
| "Device not found" | `sudo evtest` e procure por XING |
| "Permission denied" | `sudo usermod -aG input $USER` |
| "evdev not found" | `sudo apt install python3-evdev` |
| Sem notificações | `sudo apt install libnotify-bin` |
| Setas não funcionam | `sudo evtest /dev/input/event11` |
| Sem logs | Criar `~/.cache/controle_led/` |

---

## 📊 Status do Sistema

```bash
# Verificar se está rodando
ps aux | grep controle_led

# Quantos erros nos logs?
grep ERROR ~/.cache/controle_led/controle_led.log | wc -l

# Ver últimos 20 eventos
tail -20 ~/.cache/controle_led/controle_led.log
```

---

## 🚀 Instalação como Serviço (5 minutos)

```bash
# 1. Copiar script
sudo cp ~/controle_led_v2.py /usr/local/bin/controle_led
sudo chmod +x /usr/local/bin/controle_led

# 2. Criar service file
sudo nano /etc/systemd/system/controle_led.service
# (Copie o conteúdo do guia de instalação)

# 3. Habilitar
sudo systemctl daemon-reload
sudo systemctl enable controle_led
sudo systemctl start controle_led

# 4. Verificar
sudo systemctl status controle_led
```

---

## ⚙️ Variáveis Importantes (no topo do arquivo)

```python
PALETA                  # Lista de cores (nome, hex)
LONG_PRESS_TIME        # Tempo para long press (3.0)
DEVICE_ID              # ID do device OpenRGB (0)
LOG_FILE               # Arquivo de log
modo_led_ativo         # Estado do modo (True/False)
indice_cor             # Cor atual na paleta (0-9)
```

---

## 🎨 Exemplos de Customização Rápida

### Adicionar nova cor
```python
# Na lista PALETA:
("Cyan",     "00FFFF"),  # ← Aqui
```

### Remapear botão
```python
# Procure "KEY_BACK" e substitua por "KEY_HOME"
```

### Novo comportamento
```python
elif keycode == ecodes.KEY_PLAYPAUSE:
    logger.info("Play/Pause → ciclo automático")
    # sua lógica aqui
```

---

## 📱 Notificações Padrão

```
MODO LED LIGADO
  "🎨 MODO LED"
  "Ligado — use Vol+/Vol- ou Setas..."
  
COR MUDADA
  "🎨 Cor"
  "Nome da cor"
  
MODO LED DESLIGADO
  "🔕 MODO LED"
  "Desligado"
```

---

## 🔌 Dispositivos de Input

```
event11  = Teclado (OK, setas, letras)
event23  = Consumer Control (Vol+, Vol-, Back, Home)
event24  = System Control (Power, Sleep - não usado)
```

**Podem variar conforme porta USB!** O script detecta automaticamente.

---

## 💡 Dicas Úteis

```bash
# Executar em background
python3 controle_led_v2.py &

# Redirecionar output
python3 controle_led_v2.py > /tmp/led.log 2>&1 &

# Parar processo
killall python3  # ⚠️ Mata todos os Python!
kill 12345       # Melhor: mata apenas PID específico

# Encontrar PID
pgrep -f controle_led

# Reexecutar último comando
!!
```

---

## 🎯 Checklist Funcionalidades

- [ ] Long press OK funciona
- [ ] Vol+ aumenta (próxima cor)
- [ ] Vol- diminui (cor anterior)
- [ ] Setas ↑↓←→ mudam cores
- [ ] Back sai do modo
- [ ] Notificações aparecem
- [ ] Log está sendo criado
- [ ] Sem erros no console

---

## 📞 Informações Importantes

```
Script principal:  ~/Área de trabalho/PROJETOS/openrgb/controle_led_v2.py
Log de erros:      ~/.cache/controle_led/controle_led.log
Config OpenRGB:    /etc/systemd/system/controle_led.service (opcional)
Documentação:      README.md, INSTALACAO_CONTROLE_LED.md, etc
```

---

## 🎓 Leitura Rápida (5 min)

1. README.md - Visão geral (2 min)
2. INSTALACAO_CONTROLE_LED.md - Passo a passo (3 min)
3. Executar e testar! (5 min)

**Total: 15 minutos para tudo funcionando!**

---

## 🚨 Emergency Reset

Se tudo quebrou:
```bash
# Reverter para backup
cp controle_led_v2.py.backup controle_led_v2.py

# Parar tudo
sudo systemctl stop controle_led
killall python3

# Resetar LEDs para branco
openrgb --device 0 --mode static --color FFFFFF

# Começar do zero
python3 controle_led_v2.py
```

---

**Última atualização:** 2026-03-24
**Versão:** 2.0
**Status:** ✅ Pronto para produção
