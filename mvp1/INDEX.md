# 📦 Índice do Projeto - Controle de LEDs com Air Mouse LE-7278

Todos os arquivos necessários para controlar suas LEDs RGB com o controle remoto Air Mouse.

---

## 📂 Arquivos do Projeto

### 🎨 **Arquivo Principal**

#### `controle_led.py` (9.9 KB)
**O script principal do daemon**

- Auto-detecta os devices do Air Mouse pelo nome
- Escuta botões em paralelo (threading)
- Implementa long press (3 segundos) para ativar MODO LED
- Navega entre cores com Vol+/Vol-
- Envia notificações desktop
- Executa `openrgb` para mudar cores

**Como usar:**
```bash
python3 controle_led.py
# ou
python3 ~/Área\ de\ trabalho/PROJETOS/openrgb/controle_led.py
```

**Dependências:**
- `python3-evdev`
- `openrgb`
- `libnotify-bin` (para notificações)

---

### ⚙️ **Scripts de Instalação**

#### `setup_controle_led.sh` (5.8 KB)
**Instalador automático de dependências**

Faz tudo automaticamente:
1. Instala `python3-evdev` e `libnotify-bin`
2. Adiciona usuário ao grupo `input`
3. Copia script para local apropriado
4. Cria aliases `led-daemon` e `led-stop`
5. Gera arquivo de serviço systemd

**Como usar:**
```bash
chmod +x setup_controle_led.sh
./setup_controle_led.sh
```

**Depois:** Faça logout/login para aplicar mudanças do grupo input.

---

### 🔍 **Scripts de Diagnóstico**

#### `diagnostico_controle_led.sh` (6.5 KB)
**Verificação completa do sistema**

Testa:
- Todas as dependências instaladas
- Grupo `input` configurado
- Air Mouse detectado
- OpenRGB funcionando
- Notificações desktop
- Script em local correto

**Como usar:**
```bash
chmod +x diagnostico_controle_led.sh
./diagnostico_controle_led.sh
```

**Quando usar:**
- Antes de usar o daemon pela primeira vez
- Se encontrar erros
- Para validar que tudo está OK

---

#### `teste_botoes.py` (5.9 KB)
**Teste interativo dos botões**

Interface para:
1. Listar todos os Air Mouse conectados
2. Escolher qual testar
3. Ver eventos dos botões em tempo real
4. Descobrir keycodes e comportamento

**Como usar:**
```bash
chmod +x teste_botoes.py

# Modo interativo
python3 teste_botoes.py

# Teste direto de um device
python3 teste_botoes.py /dev/input/event11
```

**Útil para:**
- Descobrir qual `/dev/input/event*` é seu controle
- Ver quais botões geram quais keycodes
- Debugar problemas de reconhecimento

---

### 📚 **Documentação**

#### `QUICK_START.md` (4.3 KB)
**Guia de Início Rápido (5-10 minutos)**

Resumido e direto:
- Checklist pré-requisitos
- Passos de instalação
- Teste rápido
- Comandos para usar
- Troubleshooting básico

**Leia primeiro se:**
- Tem pressa
- Quer instalar rapidamente
- Prefere guia conciso

---

#### `README_CONTROLE_LED.md` (7.1 KB)
**Documentação Completa**

Documentação detalhada:
- Características completas
- Pré-requisitos e dependências
- Instalação passo-a-passo
- Uso completo (todos os comandos)
- Instalação como serviço systemd
- Troubleshooting detalhado
- Personalização (cores, tempo, etc)
- Guia de debug

**Leia se:**
- Quer entender tudo em profundidade
- Precisa de troubleshooting avançado
- Quer personalizar o comportamento

---

#### `PLANO_CONTROLE_LED.md` (7.3 KB)
**Especificação e Planejamento**

Arquitetura técnica:
- Ideia central (MODO LED)
- Fluxo de uso
- Dispositivos monitorados
- Detecção de long press
- Notificações desktop
- Navegação de cores
- Arquitetura do script
- Dependências
- Checklist de implementação

**Leia se:**
- Quer entender a arquitetura
- Quer modificar o código
- Tem interesse técnico

---

### ⚙️ **Arquivo de Serviço**

#### `air-mouse-leds.service` (540 bytes)
**Arquivo de serviço systemd para autostart**

Permite que o daemon inicie automaticamente:
- Ao fazer login no desktop
- Ao reiniciar o sistema
- Com restart automático se falhar

**Como usar:**
```bash
sudo cp air-mouse-leds.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable air-mouse-leds
sudo systemctl start air-mouse-leds
```

**Comandos úteis:**
```bash
# Ver status
sudo systemctl status air-mouse-leds

# Ver logs
sudo journalctl -u air-mouse-leds -f

# Parar
sudo systemctl stop air-mouse-leds

# Reiniciar
sudo systemctl restart air-mouse-leds
```

---

## 🚀 Como Começar

### 1️⃣ **Leia o Quick Start** (2 minutos)
```bash
cat QUICK_START.md
```

### 2️⃣ **Execute o Setup** (3 minutos)
```bash
chmod +x setup_controle_led.sh
./setup_controle_led.sh
```

### 3️⃣ **Faça Logout/Login**
```bash
exit  # ou exec su - $USER
```

### 4️⃣ **Conecte o Air Mouse**
Aguarde 20-60 segundos

### 5️⃣ **Execute Diagnóstico** (2 minutos)
```bash
chmod +x diagnostico_controle_led.sh
./diagnostico_controle_led.sh
```

### 6️⃣ **Teste os Botões** (1 minuto)
```bash
chmod +x teste_botoes.py
python3 teste_botoes.py
```

### 7️⃣ **Inicie o Daemon**
```bash
led-daemon
# ou
python3 controle_led.py
```

### 8️⃣ **Teste os Comandos**
- Long press OK (3s) → Ativa MODO LED
- Vol+/Vol- → Muda cores
- Back → Desativa MODO LED

---

## 📊 Resumo de Arquivos

| Arquivo | Tamanho | Tipo | Descrição |
|---------|---------|------|-----------|
| `controle_led.py` | 9.9 KB | 🐍 Python | Script principal do daemon |
| `setup_controle_led.sh` | 5.8 KB | 🔧 Script | Instalador automático |
| `diagnostico_controle_led.sh` | 6.5 KB | 🔍 Script | Verificação de sistema |
| `teste_botoes.py` | 5.9 KB | 🧪 Python | Teste interativo de botões |
| `QUICK_START.md` | 4.3 KB | 📄 Docs | Guia rápido (5-10 min) |
| `README_CONTROLE_LED.md` | 7.1 KB | 📚 Docs | Documentação completa |
| `PLANO_CONTROLE_LED.md` | 7.3 KB | 📋 Docs | Especificação técnica |
| `air-mouse-leds.service` | 540 B | ⚙️ Config | Service systemd |
| **TOTAL** | **47 KB** | 📦 | **9 arquivos** |

---

## ✅ Checklist de Instalação

- [ ] Li o QUICK_START.md
- [ ] Executei setup_controle_led.sh
- [ ] Fiz logout/login
- [ ] Conectei o Air Mouse
- [ ] Rodei diagnostico_controle_led.sh (sem erros)
- [ ] Testei botões com teste_botoes.py
- [ ] Iniciei controle_led.py
- [ ] Testei MODO LED (long press OK)
- [ ] Testei navegação de cores (Vol+/Vol-)
- [ ] Desativei MODO LED (Back ou OK 3s)

---

## 🎯 Próximos Passos Opcionais

- [ ] Instalar como serviço systemd (autostart)
- [ ] Personalizar paleta de cores
- [ ] Mudar tempo de long press
- [ ] Criar atalhos customizados
- [ ] Integrar com outras aplicações

---

## 🆘 Precisa de Ajuda?

1. **Erros durante instalação?**
   → Veja `diagnostico_controle_led.sh`

2. **Botões não respondem?**
   → Use `teste_botoes.py`

3. **LEDs não mudam?**
   → Consulte troubleshooting em `README_CONTROLE_LED.md`

4. **Quer entender tudo?**
   → Leia `PLANO_CONTROLE_LED.md`

---

## 🎉 Pronto!

Você tem tudo que precisa para controlar suas LEDs! 🎨✨

Próximo passo: execute `QUICK_START.md` e comece a usar!
