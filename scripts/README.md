# scripts/ — Guia de Uso

Utilitários de desenvolvimento, qualidade e empacotamento do projeto RGB Control.
Execute sempre a partir da **raiz do projeto** (`~/PROJETOS/Pessoal/rgb-control/`).

---

## Fluxo recomendado

```
setup_dev.sh          ← uma vez só (novo clone)
      ↓
bump_version.py       ← se for lançar nova versão (opcional)
      ↓
run_tests.sh          ← obrigatório antes de qualquer push
      ↓
atualizar.sh          ← instala no sistema (requer sudo)
      ↓
install_extension.sh  ← atualiza a extensão GNOME (sem sudo)
```

> Para o fluxo completo e interativo (escolha de cenário A/B/C), use
> `bash scripts/pipeline_run.sh` em vez de executar cada script manualmente.

---

## Scripts

### `setup_dev.sh` — Onboarding (rodar uma vez após clonar)

Instala os git hooks do projeto (commit-msg e pre-push) em `.git/hooks/`.

```bash
bash scripts/setup_dev.sh
```

**Requer:** repositório git inicializado.  
**Efeito:** copia hooks de `packaging/git-hooks/` → `.git/hooks/`.

---

### `pipeline_run.sh` — Pipeline interativo completo

Interface guiada para o fluxo completo de desenvolvimento. Apresenta 3 cenários:

| Cenário | Quando usar |
|---------|-------------|
| **A** | Correção ou feature pontual (mesma versão) |
| **B** | Lançar nova versão semântica X.Y.Z |
| **C** | Alterar apenas o empacotamento Debian (novo REV) |

```bash
bash scripts/pipeline_run.sh
```

**Inclui automaticamente:** bump de versão (se B), `run_tests.sh` e `build_deb.sh`.

---

### `bump_version.py` — Atualizar versão em todos os arquivos

Atualiza a versão semântica de forma sincronizada em todos os arquivos controlados:
`pyproject.toml`, `README.md`, `docs/stack.md`, `docs/TESTS.md`,
`src/rgb_control/main.py`, `packaging/rgb.sh` e `scripts/atualizar.sh`.

```bash
# Com argumento (não interativo — usado pelo pipeline_run.sh)
python3 scripts/bump_version.py 1.2.0

# Modo interativo (pede a versão)
python3 scripts/bump_version.py
```

> ⚠️ Após o bump, rode `./run_tests.sh` para validar a sincronia via `docs_sync_check.py`.

---

### `docs_sync_check.py` — Auditoria de sincronia de versão

Verifica se todos os arquivos controlados declaram a **mesma versão** do `pyproject.toml`.
Chamado automaticamente pelo `run_tests.sh` (Gate 6).

```bash
python3 scripts/docs_sync_check.py
```

Falha com saída não-zero se qualquer arquivo estiver desatualizado.

---

### `coverage_ratchet.py` — Ratchet de cobertura de testes

Garante que a cobertura de testes nunca regrida. Lê `coverage.json` (gerado pelo pytest)
e compara com o threshold salvo em `.coverage_ratchet_threshold`.

- Se a cobertura **subiu** → atualiza o threshold automaticamente (novo pico).
- Se a cobertura **caiu** → falha e bloqueia o commit.

```bash
# Requer que pytest --cov-report=json tenha rodado antes
python3 scripts/coverage_ratchet.py
```

Chamado automaticamente pelo `run_tests.sh` (Gate 5).

---

### `atualizar.sh` — Build + instalação local (requer `sudo`)

Executa o `build_deb.sh` e instala o pacote `.deb` gerado via `dpkg`.
Atualiza também os caches do sistema (ícones, desktop, appstream).

```bash
bash scripts/atualizar.sh
```

**Requer:** `sudo` (pedido durante a execução).  
**Efeito:** instala ou atualiza o pacote `rgb-control` no sistema.

---

### `install_extension.sh` — Instalar extensão GNOME (sem `sudo`)

Copia os arquivos de `gnome-extension/` para
`~/.local/share/gnome-shell/extensions/rgb-control@sant.github.com/`
e habilita a extensão via `gnome-extensions enable`.

```bash
bash scripts/install_extension.sh
```

> Se o GNOME Shell não recarregar automaticamente, pressione `Alt+F2` → `r`
> ou faça logout/login para ativar a extensão.

---

### `linhas_tam.sh` — Auditoria de tamanho dos arquivos

Lista todos os arquivos do projeto com tamanho em bytes e número de linhas,
excluindo binários, cache e builds.

```bash
bash scripts/linhas_tam.sh
```

> ⚠️ O path interno está hardcoded para o ambiente original. Ajuste a linha `cd`
> se o projeto estiver em outro diretório.

---

## Variáveis de ambiente relevantes

| Variável | Definido por | Descrição |
|----------|-------------|-----------|
| `PYTHONPATH` | `run_tests.sh` | Aponta para `src/` para resolução dos módulos |
| `MYPYPATH` | `run_tests.sh` | Aponta para `src/` para o mypy --strict |
| `PYTEST_CURRENT_TEST` | pytest | Detectado internamente pelo `log_viewer.py` para modo headless |
