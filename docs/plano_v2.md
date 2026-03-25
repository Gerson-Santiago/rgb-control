# Análise Profissional — mvp.py v2

## Problemas identificados no output do daemon

```
✅ Teclado → /dev/input/event10  (2.4G Wireless Device)    ← ERRADO
✅ Consumer → /dev/input/event9  (2.4G Wireless Device...) ← ERRADO
✅ Teclado → /dev/input/event3   (2.4G Wireless Device)    ← ERRADO
✅ Consumer → /dev/input/event13 (XING WEI...)             ← correto (sobrescreveu)
✅ Teclado → /dev/input/event11  (XING WEI...)             ← correto (sobrescreveu)
```

Funcionou **por acidente**. O XING WEI foi o último match e sobrescreveu os errados.

---

## 4 Melhorias Propostas

### A — Filtro por USB Vendor/Product ID
**Problema:** `"2.4g"` casa com qualquer device "2.4G Wireless".  
**Solução profissional:** identificar o hardware pelo ID USB único confirmado nos logs:

```
vendor=0x1915  product=0x1025
```

```python
# evdev: InputDevice.info retorna (bustype, vendor, product, version)
XINGWEI_VENDOR  = 0x1915
XINGWEI_PRODUCT = 0x1025

if dev.info.vendor == XINGWEI_VENDOR and dev.info.product == XINGWEI_PRODUCT:
    # é o Air Mouse LE-7278, com certeza
```

✅ Robusto: não importa quantos "2.4G" devices estejam no sistema.  
✅ Referência: [python-evdev docs — InputDevice.info](https://python-evdev.readthedocs.io/en/latest/apidoc.html#evdev.device.InputDevice.info)

---

### B — `device.grab()` — Exclusividade durante MODO LED
**Problema:** botões ainda vão para o terminal (linhas em branco = Enter chegando no tty).  
**Solução:** `grab()` intercepta os eventos exclusivamente para nosso processo.

```python
# Ao ativar MODO LED:
device_teclado.grab()    # bloqueia botões de chegarem no terminal/X11

# Ao desativar:
device_teclado.ungrab()  # devolve ao sistema
```

✅ Padrão da comunidade para key remapping e macros.  
✅ Referência: [python-evdev — grab()](https://python-evdev.readthedocs.io/en/latest/apidoc.html#evdev.device.InputDevice.grab)

> [!WARNING]
> `grab()` impede que O TECLADO FUNCIONE NORMALMENTE enquanto ativo.
> Só faz sentido durante o MODO LED, e deve sempre ter um `ungrab()` garantido no `finally`.

---

### C — asyncio em vez de threading
**Problema:** duas threads (`threading.Thread`) não é o padrão moderno para evdev.  
**Solução:** `evdev` tem suporte nativo a `asyncio` desde v1.0:

```python
# Moderno — sem threads, sem locks manuais
async def listener_teclado(dev):
    async for event in dev.async_read_loop():
        ...

async def listener_consumer(dev):
    async for event in dev.async_read_loop():
        ...

async def main():
    await asyncio.gather(
        listener_teclado(device_teclado),
        listener_consumer(device_consumer),
    )
```

✅ Um único event loop, sem race conditions.  
✅ Cancela tasks limpamente com `task.cancel()`.  
✅ Referência: [python-evdev asyncio example](https://python-evdev.readthedocs.io/en/latest/tutorial.html#reading-events-from-multiple-devices-using-asyncio)

---

### D — SIGUSR1 Toggle (Bônus — integração)
Permite ativar/desativar o MODO LED de qualquer outro script:

```python
import signal, os

PID_FILE = Path("/tmp/controle_led.pid")

# No daemon: registrar sinal
signal.signal(signal.SIGUSR1, lambda *_: alternar_modo())
PID_FILE.write_text(str(os.getpid()))

# De outro terminal ou script:
# kill -USR1 $(cat /tmp/controle_led.pid)
# ou: python3 mvp.py --toggle
```

✅ Integração fácil com Kodi, scripts de boot, aliases.

---

## Resumo — O que mudar no v2

| Item | v1 (atual) | v2 (profissional) |
|---|---|---|
| Filtro de device | string `"2.4g"` — frágil | Vendor/Product ID — robusto |
| Arquitetura | `threading.Thread` | `asyncio.gather` |
| Teclas durante MODO LED | passam para o terminal | bloqueadas com `grab()` |
| Ativação externa | só long press | + SIGUSR1 (`--toggle`) |

---

## Fontes / Documentação

- [python-evdev docs](https://python-evdev.readthedocs.io/)
- [evdev asyncio tutorial](https://python-evdev.readthedocs.io/en/latest/tutorial.html#reading-events-from-multiple-devices-using-asyncio)
- [Linux Input Subsystem userspace API](https://www.kernel.org/doc/html/latest/input/input_uapi.html)
- [asyncio — Python 3 docs](https://docs.python.org/3/library/asyncio.html)
