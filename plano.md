# 🎮 LEDs do Gabinete via Controle Lelong LE-7678

## 📌 Contexto

O controle Lelong LE-7678 (LE-7278) conecta via **USB dongle 2.4GHz** e é reconhecido no Linux automaticamente como um **teclado HID** (`/dev/input/eventX`). Sem instalar driver nenhum.

A ideia: capturar os botões com Python (`evdev`) e acionar o `openrgb` para mudar as cores dos LEDs do gabinete.

---

## 🏗️ Arquitetura

```
Controle (USB dongle)
       │
       ▼
/dev/input/eventX  (teclado HID — kernel já reconhece)
       │
       ▼
controle_led.py  ← daemon Python
       │  lê keycodes via evdev
       │  consulta mapeamento botão → cor
       ▼
openrgb --device 0 --mode static --color HEX
       │
       ▼
💡 LEDs do gabinete mudam de cor
```

---

## 🗂️ Arquivos do Projeto

| Arquivo | Status | Função |
|---|---|---|
| `rbg.sh` | ✅ pronto | CLI/menu interativo de cores |
| `controle_led.py` | 🔲 a criar | daemon Python — controle → LEDs |
| `plano.md` | 📋 este arquivo | documentação |

---

## 🎨 Mapeamento de Botões (proposta)

| Botão | Cor | HEX |
|---|---|---|
| `1` | 🔴 Vermelho | `FF0000` |
| `2` | 🟢 Verde | `00FF00` |
| `3` | 🔵 Azul | `0000FF` |
| `4` | 🟡 Amarelo | `FFFF00` |
| `5` | 🟠 Laranja | `FF5500` |
| `6` | 🟡 Âmbar | `FFB200` |
| `7` | 🌟 Branco | `FFFFFF` |
| `8` | 🩵 Ciano | `00F2EA` |
| `9` | 🟣 Roxo | `AA00FF` |
| `0` | ⚫ Desligar | `000000` |
| `Home` | 🌟 Branco (padrão) | `FFFFFF` |
| `Volume+` | ➡️ Próxima cor | — |
| `Volume-` | ⬅️ Cor anterior | — |

> Os keycodes reais são confirmados na **Fase 1** com `evtest`.

---

## 📋 Fases de Implementação

### Fase 1 — Diagnóstico do controle (você faz isso)

Com o **dongle USB plugado**:

```bash
# Ver os dispositivos de entrada disponíveis
sudo evtest

# Selecionar o device do controle (provavelmente "BT-REMOTE" ou "Lelong")
# Pressionar cada botão para ver o keycode real
```

Anote os keycodes dos botões que quer usar.

---

### Fase 2 — Implementação do daemon Python

```bash
# Instalar dependência
sudo apt install python3-evdev

# Adicionar usuário ao grupo input (evitar sudo)
sudo usermod -aG input $USER
# ⚠️ Precisa fazer logout/login após isso
```

O script `controle_led.py` vai:
- Auto-detectar o device pelo nome
- Escutar eventos de tecla em loop
- Chamar `openrgb` quando um botão mapeado for pressionado

---

### Fase 3 — Integração (opcional)

```bash
# Iniciar manualmente
python3 controle_led.py

# Ou via alias
alias led-daemon='python3 /home/sant/Área\ de\ trabalho/PROJETOS/openrbg/controle_led.py'
```

Futuramente: serviço systemd para iniciar automaticamente no boot.

---

## ✅ Checklist

- [x] Projeto `openrbg` existente com `rbg.sh` funcionando
- [x] Entender arquitetura (evdev → openrgb)
- [ ] **Fase 1**: rodar `evtest` com controle plugado e mapear keycodes
- [ ] **Fase 2**: criar `controle_led.py`
- [ ] **Fase 2**: testar daemon manualmente
- [ ] **Fase 3**: integrar alias / systemd (opcional)

---

## 📦 Dependências

```bash
python3-evdev   # leitura de eventos HID
openrgb         # já instalado ✅
```