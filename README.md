# openrbg — Controle de LEDs via Air Mouse 🎨🎮🐧

Daemon Python para controlar LEDs do gabinete **ASUS TUF Gaming** usando um **Air Mouse XING WEI 2.4G USB** (Lelong LE-7278) no Linux.

## Requisitos

```bash
sudo apt install python3-evdev dunst
```

> O **dunst** é necessário para o OSD visual (modal de ativação como o indicador de volume).

## Uso

```bash
# Iniciar o daemon (requer root para ler /dev/input/event*)
sudo python3 mvp.py

# Controlar via CLI
python3 mvp.py --toggle   # Alterna MODO LED
python3 mvp.py --status   # Mostra estado atual
python3 mvp.py --list     # Lista devices detectados
```

## Botões do Controle

| Botão | Ação |
|---|---|
| 🎙️ **Microfone** | Ativar / Desativar MODO LED |
| 🏠 **Home** | Ativar / Desativar MODO LED |
| ➡️ Seta Direita / ➕ Vol+ | Próxima cor |
| ⬅️ Seta Esquerda / ➖ Vol− | Cor anterior |
| ↩️ Back | Desativar MODO LED |
| **OK (3s)** | Toggle (fallback) |

## Paleta de Cores

| Índice | Nome | Hex |
|---|---|---|
| 0 | Vermelho | `FF0000` |
| 1 | Laranja | `FF5500` |
| 2 | Amarelo | `FFFF00` |
| 3 | Verde | `00FF00` |
| 4 | Ciano | `00F2EA` |
| 5 | Azul | `0000FF` |
| 6 | Roxo | `AA00FF` |
| 7 | Âmbar | `FFB200` |
| 8 | Branco | `FFFFFF` |
| 9 | Desligar | `000000` |

## Hardware Detectado

- **Vendor ID:** `0x1915` / **Product ID:** `0x1025`
- **Teclado:** `/dev/input/event11` — XING WEI 2.4G USB USB Composite Device
- **Consumer Control:** `/dev/input/event13` — XING WEI 2.4G USB USB Composite Device Consumer Control

## Testes

```bash
python3 -m pytest tests/ -v
```

### 🛠️ Desenvolvimento & Qualidade

O projeto utiliza uma arquitetura de QA **Gold Standard (v1.0.22)**, com blindagem de cobertura, testes de propriedade e monitoramento de memória.

-   **Manual de Testes**: Consulte [docs/TESTS.md](docs/TESTS.md) para detalhes técnicos exaustivos.
-   **Suite de Testes**: Execute o gate de qualidade com `./run_tests.sh`.
-   **Dependências de QA**:
    ```bash
    pip install pytest-cov pytest-asyncio hypothesis pyfakefs mypy pyright
    ```

### 🤝 Contribuição
1.  Faça um fork do projeto.
2.  Crie uma branch para sua modificação (`git checkout -b feature/nova-feature`).
3.  **Certifique-se de passar no Portão de Qualidade** (`./run_tests.sh`) antes de enviar.
4.  Envie um Pull Request.

## Estrutura

```
openrbg/
├── mvp.py          # Daemon principal
├── rbg.sh          # Script de aplicação de cores (OpenRGB)
├── tests/
│   └── test_mvp.py # Suite de testes (pytest)
├── docs/
│   ├── log1.md     # evtest event11 (teclado)
│   └── log2.md     # evtest event13 (consumer)
└── requirements.txt
```
