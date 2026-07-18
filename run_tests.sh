#!/usr/bin/env bash
# Pipeline Reference: .agents/workflows/pipeline.md
# run_tests.sh - Executado antes do build_deb.sh ou git push
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"

# shellcheck source=scripts/lib/shell_ui.sh
source "$SCRIPT_DIR/scripts/lib/shell_ui.sh"

step() { echo -e "\n${BOLD}${CYAN}── $1 ──${RESET}"; }
ok()   { echo -e "  ${OK} $1"; }
fail() { echo -e "  ${FAIL} ${RED}$1${RESET}"; }
warn() { echo -e "  ${WARN} ${YELLOW}$1${RESET}"; }

ui_banner "🧪  Pipeline Local de Qualidade         "

# ── Gate 0: arquivos de teste não rastreados ──────────────────────────────────
step "Gate 0 — Arquivos de teste não rastreados"
UNTRACKED_TESTS=$(git ls-files --others --exclude-standard 'tests/**/*.py' 2>/dev/null || true)
if [[ -n "$UNTRACKED_TESTS" ]]; then
    warn "Arquivos de teste novos encontrados fora do git (use 'git add'):"
    echo "$UNTRACKED_TESTS" | while IFS= read -r f; do echo "       $f"; done
    fail "Abortando: faça 'git add' nos arquivos acima antes de continuar."
    exit 1
fi
ok "Nenhum arquivo de teste não rastreado."

# ── Gate 1: Pyright ───────────────────────────────────────────────────────────
step "Gate 1 — Pyright (type checking)"
pyright src/
ok "Pyright: 0 erros"

# ── Gate 2: Mypy --strict ─────────────────────────────────────────────────────
step "Gate 2 — Mypy --strict"
MYPYPATH=src python3 -m mypy --strict -p rgb_config
ok "Mypy: 0 issues"

# ── Gate 3: Bash CLI ─────────────────────────────────────────────────────────
step "Gate 3 — Bash CLI tests"
./tests/integration/test_rgb_cli.sh
ok "Bash CLI tests: OK"

# ── Gate 4: Suíte pytest + coverage ──────────────────────────────────────────
step "Gate 4 — Pytest + Coverage"

# Lê o threshold atual do ratchet (evita hardcode desatualizado)
RATCHET_FILE="$SCRIPT_DIR/.coverage_ratchet_threshold"
RATCHET_THRESHOLD=65
if [[ -f "$RATCHET_FILE" ]]; then
    RATCHET_THRESHOLD=$(python3 -c "import math; print(math.floor(float(open('$RATCHET_FILE').read())))")
fi

echo -e "  Threshold do ratchet: ${BOLD}${RATCHET_THRESHOLD}%${RESET} (floor inteiro — ratchet decimal no Gate 5)"

python3 -m pytest tests/ \
    -v \
    --tb=short \
    --cov=src \
    --cov-branch \
    --cov-report=json \
    --cov-report=term-missing:skip-covered \
    --cov-fail-under="${RATCHET_THRESHOLD}" \
    -p no:warnings

ok "Pytest: todos os testes passaram e cobertura ≥ ${RATCHET_THRESHOLD}%"

# ── Gate 5: Coverage Ratchet ──────────────────────────────────────────────────
step "Gate 5 — Coverage Ratchet"
python3 scripts/coverage_ratchet.py

# ── Gate 6: Auditoria de Versionamento ───────────────────────────────────────
step "Gate 6 — Sincronia de versão"
python3 scripts/docs_sync_check.py
ok "Versão sincronizada"

# ── Sumário final ─────────────────────────────────────────────────────────────
ui_banner "🚀  Todos os gates passaram! Pronto para empacotar."
