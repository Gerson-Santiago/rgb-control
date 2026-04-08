# Stack Tecnológica e Padrões de Projeto (v1.1)

Este documento serve como a **"Fonte Única de Verdade"** para a infraestrutura técnica do projeto `openrgb`. 

> [!IMPORTANT]
> Este documento é auditado automaticamente pelo script `scripts/docs_sync_check.py`. Descompassos de versão ou dependências causarão falha no Gate de Qualidade.

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

## 📐 Padrões de Codificação e Design

### Arquitetura (Clean Architecture)
Seguimos a separação estrita de camadas para garantir testabilidade:
1.  **Domain**: Regras puras.
2.  **Application**: Casos de uso.
3.  **Infrastructure**: Acesso a hardware e arquivos.
4.  **Presentation**: Interface gráfica reativa.

### Convenção de Commits Documentais
Para garantir rastreabilidade, use o padrão:
```bash
docs(stack): atualização da stack para v<versão> - <descrição breve>
```

---

## 📝 Notas de Migração (Legacy MVP -> Gold)

Se você está acostumado com a versão inicial (`mvp.py`), atente-se às mudanças:
-   **Remoção do `mvp.py`**: A lógica foi dividida entre `src/rgb_control` (GUI) e `src/rgb_daemon` (Lógica remota).
-   **Configuração via Constantes**: Caminhos de arquivos de status não são mais hardcoded; use as constantes em `backend.py`.
-   **Eventos Evdev**: A descoberta do Air Mouse agora é dinâmica e resiliente a mudanças de `/dev/input/eventX`.

---

## ✅ Checklist de Inclusão (Manutenção)

Sempre que adicionar uma nova dependência ou funcionalidade core, verifique:
1.  [ ] **`pyproject.toml`**: Adicione a dependência em `dependencies` ou `optional-dependencies`.
2.  [ ] **`docs/stack.md`**: Atualize as tabelas de tecnologias e dependências de runtime.
3.  [ ] **`scripts/docs_sync_check.py`**: Verifique se a nova versão está sincronizada.
4.  [ ] **`build_deb.sh`**: Atualize o campo `Depends` no arquivo `DEBIAN/control` gerado.

---

## 🏗️ Processos Operacionais

### 1. Build do Pacote (.deb)
```bash
./build_deb.sh
sudo apt install ./builds/rgb-control_$(cat version)-1_all.deb
```

### 2. Deploy do Serviço
```bash
sudo systemctl enable openrgb.service
sudo systemctl start openrgb.service
```
