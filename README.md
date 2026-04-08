# openrbg — Controle Desktop Moderno para Gabinetes Gaming 🎨🎮🐧

![Version](https://img.shields.io/badge/version-1.0.22-blue)
![Quality Gate](https://img.shields.io/badge/quality--gate-passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-73%25-success)

Solução profissional (v1.0.22) para controlar a iluminação de gabinetes **ASUS TUF Gaming** e periféricos, integrando um **Air Mouse XING WEI 2.4G USB** (Lelong LE-7278) como controle remoto nativo no Linux.


Construído com **Python 3.13**, **GTK4 / Libadwaita** e **Clean Architecture**.

---

## ✨ Funcionalidades Principais
-   **Interface Premium**: Interface gráfica moderna baseada em GNOME/Libadwaita.
-   **Controle Dual**: Gerenciamento via GUI (Janela) ou CLI (Terminal).
-   **Remoto Air Mouse**: Mapeamento de botões de controle remoto para alternar cores e estados.
-   **OSD (Dunst)**: Feedback visual na tela ao alternar modos de LED.
-   **Alta Fidelidade**: Suite de testes com 66+ validações (Property-based, Memory Stress, Contract).

## 🚀 Instalação e Requisitos

### Dependências de Sistema
```bash
sudo apt install python3-evdev python3-gi libadwaita-1-0 dunst openrgb
```

### Instalação (Padrão Debian)
Baixe o último release `.deb` e instale:
```bash
sudo apt install ./builds/rgb-control_1.0.22-1_all.deb
```

## 🎮 Operação com Air Mouse

| Botão | Ação |
|---|---|
| 🎙️ / 🏠 | Ativar / Desativar MODO LED |
| ➡️ / ➕ Vol+ | Próxima cor |
| ⬅️ / ➖ Vol− | Cor anterior |
| ↩️ Back | Desativar MODO LED |

## 🛠️ Desenvolvimento e Qualidade

Este projeto segue padrões de **QA Gold Standard**. Para contribuir ou rodar em modo desenvolvedor:

1.  **Manual Técnico de Stack**: Consulte [docs/stack.md](docs/stack.md).
2.  **Guia de Blindagem de Testes**: Consulte [docs/TESTS.md](docs/TESTS.md).
3.  **Portão de Qualidade**: Execute `./run_tests.sh` para validar toda a arquitetura.

### Setup de Desenvolvimento
```bash
git clone https://github.com/Gerson-Santiago/rgb-control.git
pip install -e .[dev]
./run_tests.sh
```

---

## 🏗️ Estrutura do Projeto
-   **`src/rgb_control/`**: Aplicação de interface gráfica (GTK4).
-   **`src/rgb_daemon/`**: Daemon de monitoramento de hardware e evdev.
-   **`tests/`**: Suite exaustiva de testes automatizados.
-   **`docs/`**: Documentação técnica detalhada.

---
**Status: ESTÁVEL & BLINDADO 🛡️**
