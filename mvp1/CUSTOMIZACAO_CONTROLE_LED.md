# 🎨 Guia de Customização do Controle de LEDs

## 1️⃣ Mudar a Paleta de Cores

Edite o arquivo `controle_led_v2.py` e procure por:

```python
PALETA = [
    ("Vermelho",   "FF0000"),
    ("Laranja",    "FF5500"),
    ("Amarelo",    "FFFF00"),
    ("Verde",      "00FF00"),
    ("Ciano",      "00F2EA"),
    ("Azul",       "0000FF"),
    ("Roxo",       "AA00FF"),
    ("Ambar",      "FFB200"),
    ("Branco",     "FFFFFF"),
    ("Desligar",   "000000"),
]
```

### Exemplo: Adicionar Pink Neon
```python
PALETA = [
    ("Vermelho",   "FF0000"),
    ("Pink Neon",  "FF10F0"),  # ← nova cor
    ("Amarelo",    "FFFF00"),
    # ... resto
]
```

### Exemplo: Remover cores
```python
PALETA = [
    ("Vermelho",   "FF0000"),
    ("Verde",      "00FF00"),
    ("Azul",       "0000FF"),
    ("Branco",     "FFFFFF"),
    ("Desligar",   "000000"),
]
```

### Dica: Encontrar cores em HEX
- 🌐 [https://www.color-hex.com](https://www.color-hex.com)
- 🎨 [https://htmlcolorcodes.com](https://htmlcolorcodes.com)
- 💻 Use: `printf "#%s\n" FFFFFF` para confirmar formato

---

## 2️⃣ Mudar Duração do Long Press

Procure por:
```python
LONG_PRESS_TIME = 3.0
```

**Exemplos:**
```python
LONG_PRESS_TIME = 2.0   # 2 segundos (mais rápido)
LONG_PRESS_TIME = 5.0   # 5 segundos (mais lento)
LONG_PRESS_TIME = 1.5   # 1.5 segundos (bem rápido)
```

---

## 3️⃣ Remapear Botões

### Entender os Key Codes

Cada botão tem um código em `evdev.ecodes`. Lista de códigos comuns:

| Botão | Código | Módulo |
|---|---|---|
| OK/Enter | `KEY_ENTER` | event11 |
| Seta cima | `KEY_UP` | event11 |
| Seta baixo | `KEY_DOWN` | event11 |
| Seta esquerda | `KEY_LEFT` | event11 |
| Seta direita | `KEY_RIGHT` | event11 |
| Volume + | `KEY_VOLUMEUP` | event23 |
| Volume - | `KEY_VOLUMEDOWN` | event23 |
| Back/Voltar | `KEY_BACK` | event23 |
| Home | `KEY_HOMEPAGE` | event23 |
| Play/Pause | `KEY_PLAYPAUSE` | event23 |
| Mute | `KEY_MUTE` | event23 |

**Como descobrir novos botões:**
```bash
# Ver todos os eventos do controle
sudo evtest /dev/input/event11
# (ou event23)

# Pressione botões e veja o KEY_* correspondente
```

### Exemplo: Mudar "Back" para "Home"

**Antes:**
```python
elif keycode == ecodes.KEY_BACK:
    logger.info("Back → desativar MODO LED")
    alternar_modo()
```

**Depois:**
```python
elif keycode == ecodes.KEY_HOMEPAGE:  # Mudou KEY_BACK para KEY_HOMEPAGE
    logger.info("Home → desativar MODO LED")
    alternar_modo()
```

---

## 4️⃣ Adicionar Novos Botões

### Exemplo: Play/Pause reseta para cor padrão

**No método `thread_consumer()`:**
```python
elif keycode == ecodes.KEY_PLAYPAUSE:
    logger.info("Play/Pause → resetar para Branco")
    global indice_cor
    indice_cor = 8  # Índice da cor Branco na PALETA
    nome, cor = PALETA[indice_cor]
    aplicar_cor(cor, nome)
    notificar("🎨 Reset", "Cor padrão restaurada", "low", 1500)
```

### Exemplo: Home reseta para primeira cor

```python
elif keycode == ecodes.KEY_HOMEPAGE:
    logger.info("Home → resetar para primeira cor")
    global indice_cor
    indice_cor = 0  # Primeira cor (Vermelho)
    nome, cor = PALETA[indice_cor]
    aplicar_cor(cor, nome)
    notificar("🎨 Reset", nome, "low", 1500)
```

---

## 5️⃣ Adicionar Ciclo Automático de Cores

### Exemplo: Mute ativa ciclo automático a cada 2 segundos

**No início do arquivo, adicione:**
```python
import threading
import time

ciclo_ativo = False

def ciclo_cores_automatico():
    """Alterna cores a cada 2 segundos"""
    global ciclo_ativo
    
    while ciclo_ativo:
        mudar_cor(1)
        time.sleep(2)  # Espera 2 segundos

def toggle_ciclo():
    """Liga/desliga ciclo automático"""
    global ciclo_ativo
    
    with lock:
        ciclo_ativo = not ciclo_ativo
        
        if ciclo_ativo:
            logger.info("🔄 Ciclo automático LIGADO")
            notificar("🔄 Ciclo", "Ativado - cores mudam a cada 2s", "normal", 2000)
            t = threading.Thread(target=ciclo_cores_automatico, daemon=True)
            t.start()
        else:
            logger.info("⏹️  Ciclo automático DESLIGADO")
            notificar("⏹️  Ciclo", "Desativado", "low", 1500)
```

**E no `thread_consumer()`, adicione:**
```python
elif keycode == ecodes.KEY_MUTE:
    logger.info("Mute → toggle ciclo automático")
    toggle_ciclo()
```

---

## 6️⃣ Mudar Notificações

### Desabilitar notificações
**Comentar o `notificar()`:**
```python
def mudar_cor(delta: int):
    # ...
    if aplicar_cor(cor, nome):
        # notificar("🎨 Cor", nome, "low", 1500)  # Comentado
        logger.info(f"Cor: {nome}")
```

### Customizar mensagens

**Antes:**
```python
notificar(
    "🎨 MODO LED",
    "Ligado — use Vol+/Vol- ou Setas para mudar as cores",
    "normal",
    3000
)
```

**Depois:**
```python
notificar(
    "🎮 LED Activado",
    "Ready! Usa los botones para cambiar colores",
    "normal",
    3000
)
```

### Mudar tempo de expiração
```python
notificar("🎨 Cor", nome, "low", 1500)
#                                 ^^^^
#                              em milissegundos
```

---

## 7️⃣ Mudar Comportamento em MODO LED

### Fazer setas navegarem cores independente de MODO LED

**Antes (setas navegam sempre):**
```python
elif value == 1:  # Apenas quando pressionado
    if keycode in (ecodes.KEY_RIGHT, ecodes.KEY_UP):
        logger.debug("Seta direita/cima → próxima cor")
        mudar_cor(1)
    elif keycode in (ecodes.KEY_LEFT, ecodes.KEY_DOWN):
        logger.debug("Seta esquerda/baixo → cor anterior")
        mudar_cor(-1)
```

**Depois (só em MODO LED):**
```python
elif value == 1 and modo_led_ativo:  # Apenas em MODO LED
    if keycode in (ecodes.KEY_RIGHT, ecodes.KEY_UP):
        logger.debug("Seta direita/cima → próxima cor")
        mudar_cor(1)
    elif keycode in (ecodes.KEY_LEFT, ecodes.KEY_DOWN):
        logger.debug("Seta esquerda/baixo → cor anterior")
        mudar_cor(-1)
```

---

## 8️⃣ Adicionar Modo Especial: Rainbow

### Fazer um ciclo infinito de cores

```python
def modo_rainbow(duracao_segundos: float = 60):
    """Ciclo de cores por N segundos"""
    inicio = time.time()
    
    while time.time() - inicio < duracao_segundos:
        mudar_cor(1)
        time.sleep(0.5)  # Muda cor a cada 0.5s
    
    logger.info("🌈 Ciclo Rainbow terminou")
    notificar("🌈 Rainbow", "Finalizado", "low", 1500)
```

**Usar com um botão:**
```python
elif keycode == ecodes.KEY_PLAYPAUSE:
    logger.info("Play/Pause → iniciar modo Rainbow por 30s")
    notificar("🌈 Rainbow", "Iniciado! Cores vão mudar por 30s", "normal", 2000)
    threading.Thread(target=lambda: modo_rainbow(30), daemon=True).start()
```

---

## 9️⃣ Debug: Ver Todos os Eventos

Adicione ao `thread_teclado()`:

```python
# Descomente para ver TODOS os eventos:
# logger.debug(f"Event: code={keycode} value={value}")

# Ou apenas não-ignorados:
if keycode not in (ecodes.KEY_ENTER, ecodes.KEY_UP, ...):
    logger.debug(f"Evento ignorado: {keycode}")
```

---

## 🔟 Exemplo Completo: Configuração Avançada

```python
# PALETA customizada
PALETA = [
    ("Vermelho 🔴",   "FF0000"),
    ("Verde 🟢",      "00FF00"),
    ("Azul 🔵",       "0000FF"),
    ("Amarelo 🟡",    "FFFF00"),
    ("Purple 💜",     "AA00FF"),
    ("Branco ⚪",     "FFFFFF"),
    ("OFF ⚫",        "000000"),
]

# Mais rápido: 2 segundos
LONG_PRESS_TIME = 2.0

# Notificações curtas: 1 segundo
notificar("🎨 Cor", nome, "low", 1000)

# Setas só funcionam em MODO LED
# Vol+/Vol- navegam sempre
```

---

## 📝 Checklist de Customização

- [ ] Testou a paleta customizada
- [ ] Duração do long press ok
- [ ] Botões remapeados conforme queria
- [ ] Notificações customizadas
- [ ] Novos comportamentos adicionados
- [ ] Log funcionando corretamente

---

## 💾 Backup de Configuração

Antes de fazer alterações grandes:
```bash
cp controle_led_v2.py controle_led_v2.py.backup
# Agora pode editar sem medo!

# Para reverter:
cp controle_led_v2.py.backup controle_led_v2.py
```

---

## 🆘 Dúvidas?

Se algo não funcionar:
```bash
# Ver qual device é qual
sudo evtest | grep XING

# Ver logs detalhados
tail -f ~/.cache/controle_led/controle_led.log

# Testar eventos manualmente
sudo evtest /dev/input/event11
# (pressione botões e veja os KEY_* codes)
```
