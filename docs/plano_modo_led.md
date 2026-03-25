# 🎨 Plano — MODO LED

## Ideia Central

Pressionar **OK por 3 segundos** ativa/desativa um "MODO LED".

- Quando **ligado**: Vol+ e Vol- navegam entre as cores dos LEDs do gabinete.
- Quando **desligado**: Vol+ e Vol- voltam ao comportamento normal do sistema (volume do som).
- Uma notificação visual aparece no Debian a cada troca de estado.

---

## Fluxo de Uso

```
[Usuário segura OK por 3s]
        │
        ▼
┌─────────────────────┐
│  MODO LED = LIGADO  │  ← notify-send: "🎨 MODO LED Ligado"
└─────────────────────┘
        │
   Vol+ / Vol-  ou  ← →  (setas)
        │
        ▼
  muda cor do LED (navega na paleta)
        │
   [OK por 3s]  ou  [Back]
        │
        ▼
┌──────────────────────┐
│  MODO LED = DESLIGADO│  ← notify-send: "🔕 MODO LED Desligado"
└──────────────────────┘
```

---

## Dispositivos monitorados

Dois devices do mesmo dongle USB lidos **em paralelo** (threads):

| Device | Tipo | Função aqui |
|---|---|---|
| `event11` | Teclado principal | Long press **OK** + setas **← →** (e ↑↓) |
| `event23` | Consumer Control | **Vol+**, **Vol-**, **Back** |

> Atenção: os números `event11` e `event23` foram confirmados nos logs do `evtest`. Porém, se o dongle for em outra porta USB, podem mudar. O script vai buscar pelo **nome** do device (`XING WEI 2.4G USB`) para ser robusto.

---

## Detecção de Long Press (3 segundos)

`evdev` emite 3 tipos de valor para `EV_KEY`:
- `value=1` → tecla pressionada (down)
- `value=2` → tecla mantida (repeat, a cada 33ms)
- `value=0` → tecla solta (up)

**Estratégia de long press:**

```
ao receber KEY_ENTER value=1:
    registrar t_inicio = agora()

ao receber KEY_ENTER value=0 (soltar):
    duracao = agora() - t_inicio
    se duracao >= 3.0s:
        → alternar MODO LED
    senão:
        → ignorar (press curto = OK normal, não faz nada)
```

Isso é mais limpo do que usar os repeats para contar.

---

## Notificação Desktop

Usar `notify-send` (nativo do Debian/GNOME/KDE, sem dependências extras):

```bash
# Ligar
notify-send "🎨 MODO LED" "Ligado — use Vol+/Vol- para mudar as cores" \
  --icon=preferences-color --urgency=normal --expire-time=3000

# Desligar
notify-send "🔕 MODO LED" "Desligado" \
  --icon=preferences-color --urgency=low --expire-time=2000
```

No Python via `subprocess.run(["notify-send", ...])` — sem bibliotecas extras.

---

## Navegação de Cores (Vol+/Vol- e Setas ←→)

Paleta ordenada (lista cíclica):

```python
PALETA = [
    ("Vermelho",  "FF0000"),
    ("Laranja",   "FF5500"),
    ("Amarelo",   "FFFF00"),
    ("Verde",     "00FF00"),
    ("Ciano",     "00F2EA"),
    ("Azul",      "0000FF"),
    ("Roxo",      "AA00FF"),
    ("Ambar",     "FFB200"),
    ("Branco",    "FFFFFF"),
    ("Desligar",  "000000"),
]
```

### Botões de navegação (todos fazem a mesma coisa):

| Botão | Device | Ação |
|---|---|---|
| `Vol+` | event23 | ➡️ próxima cor |
| `Vol-` | event23 | ⬅️ cor anterior |
| `→` (seta direita) | event11 | ➡️ próxima cor |
| `←` (seta esquerda) | event11 | ⬅️ cor anterior |
| `↑` (seta cima) | event11 | ➡️ próxima cor |
| `↓` (seta baixo) | event11 | ⬅️ cor anterior |

- Cíclico (do final volta ao início e vice-versa)
- Cada mudança chama `openrgb --device 0 --mode static --color HEX`
- `notify-send` mostra o nome da cor brevemente (1.5s)

---

## Back como atalho de saída

No `event23`, `KEY_BACK` é o botão "voltar" do controle.

Comportamento proposto:
- **Dentro do MODO LED**: `Back` desativa o modo imediatamente (sem esperar 3s)
- **Fora do MODO LED**: `Back` ignorado pelo daemon

---

## Arquitetura do Script (`controle_led.py`)

```
controle_led.py
├── buscar_devices()         → acha event11 e event23 pelo nome
├── thread_teclado()         → monitora event11 (long press OK + setas ←→↑↓)
├── thread_consumer()        → monitora event23 (Vol+, Vol-, Back)
├── alternar_modo()          → liga/desliga MODO LED + notify-send
├── mudar_cor(delta)         → avança/recua na paleta + openrgb
└── loop principal           → junta as threads via threading
```

---

## Dependências

| Pacote | Instalação |
|---|---|
| `python3-evdev` | `sudo apt install python3-evdev` |
| `libnotify-bin` | `sudo apt install libnotify-bin` (notify-send) |
| `openrgb` | já instalado ✅ |

**Grupo input** (para não precisar de sudo):
```bash
sudo usermod -aG input $USER
# logout/login necessário depois
```

---

## Checklist de Implementação

- [ ] Instalar `python3-evdev` e `libnotify-bin`
- [ ] Adicionar usuário ao grupo `input`
- [ ] Criar `controle_led.py` com:
  - [ ] Auto-detecção de devices por nome
  - [ ] Long press OK (3s) → alternar modo
  - [ ] Vol+ / Vol- → navegar paleta (apenas no MODO LED)
  - [ ] Back → desativar modo
  - [ ] notify-send nas transições
- [ ] Testar manualmente
- [ ] Alias: `alias led-ctrl='python3 ~/...controle_led.py &'`
