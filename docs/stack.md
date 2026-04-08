# Stack Tecnológica e Padrões de Projeto (v1.0.22)

Este documento serve como a **"Fonte Única de Verdade"** para a infraestrutura técnica do projeto `openrbg`. Ele organiza a stack, dependências, padrões de codificação e processos operacionais.

---

## 🛠️ Stack Tecnológica (Core)

| Componente | Tecnologia | Versão Mínima | Finalidade |
| :--- | :--- | :--- | :--- |
| **Linguagem** | Python | 3.13 | Lógica core, daemon e GUI |
| **GUI Framework** | GTK4 / Libadwaita | 4.0 / 1.0 | Interface moderna e responsiva |
| **Runtime Bindings** | PyGObject (gi) | 3.44 | Ponte entre Python e C (GTK/Adw) |
| **Hardware I/O** | python-evdev | 1.6 | Leitura direta de eventos de mouse/teclado |
| **Hardware Backend** | OpenRGB | 0.9 | Driver de controle de LEDs (via CLI) |
| **IPC & Sinais** | D-Bus / POSIX | - | Comunicação entre GUI, Daemon e Systemd |

---

## 📦 Dependências e Requisitos

### Runtime (Produção)
Para rodar o sistema no Linux (Debian/Ubuntu):
- `python3-evdev`: Leitura do Air Mouse.
- `python3-gi`: Bindings do GTK4.
- `libadwaita-1-0`: Componentes visuais GNOME modernos.
- `dunst`: Notificações OSD (On-Screen Display).
- `openrgb`: Backend de controle de hardware.
- `pkexec` (PolicyKit): Elevação de privilégios para acesso ao hardware.

### Desenvolvimento (QA)
Instaladas via `pip install .[dev]`:
- `pytest-cov`, `pytest-asyncio`, `pytest-mock`, `pyfakefs`.
- `hypothesis`: Testes de propriedade.
- `mypy`, `pyright`: Checagem estática de tipos.
- `ruff`, `black`: Formatação e linting.

---

## 📐 Padrões de Codificação e Design

### Arquitetura (Clean Architecture)
Seguimos rigorosamente a separação de camadas:
1.  **Domain**: Regras de negócio puras (ex: lógica de cores, estados da ventoinha). Sem dependências externas.
2.  **Application**: Casos de uso (ex: alternar modo LED, navegar na paleta). Orquestra os serviços.
3.  **Infrastructure**: Implementações concretas (ex: chamadas `subprocess` para OpenRGB, leitura de `/dev/input`).
4.  **Presentation (GUI)**: Camada Libadwaita reativa e isolada.

### Nomenclatura e Estilo
- **PEP 8**: Seguido via Ruff/Black.
- **Classes**: `PascalCase` (Ex: `MainWindow`, `RgbDaemon`).
- **Funções/Variáveis**: `snake_case` (Ex: `update_status_ui`, `hex_val`).
- **Constantes**: `UPPER_SNAKE_CASE` (Ex: `STATUS_FILE`).
- **Tipagem**: `Type Hints` obrigatórios e estritos (`mypy --strict`).

---

## 🏗️ Processos de Build, Setup e Deploy

### 1. Setup de Desenvolvimento
```bash
git clone https://github.com/Gerson-Santiago/rgb-control.git
pip install -e .[dev]
```

### 2. Execução Local (Modo Dev)
```bash
PYTHONPATH=src python3 src/rgb_control/main.py   # Roda a GUI
PYTHONPATH=src python3 src/rgb_daemon/main.py    # Roda o Daemon
```

### 3. Build do Pacote (.deb)
O script `build_deb.sh` automatiza a criação do instalador Debian:
```bash
./build_deb.sh
sudo apt install ./builds/rgb-control_1.0.22-1_all.deb
```

### 4. Deploy do Serviço
O daemon deve rodar como um serviço de sistema para persistência:
```bash
sudo systemctl enable openrbg.service
sudo systemctl start openrbg.service
```

---

## 🔄 Manutenção da Documentação

Para manter este documento útil:
1.  **Sincronização de Versão**: Sempre que atualizar o `pyproject.toml`, verifique se o cabeçalho deste arquivo reflete a nova versão.
2.  **Novas Deps**: Qualquer `import` de biblioteca externa deve ser registrado na seção de Dependências.
3.  **Refatoração**: Se mudar a topologia de pastas em `src/`, atualize a seção de Arquitetura.
