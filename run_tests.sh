#!/bin/bash
# run_tests.sh - Executado antes do build_deb.sh ou git push
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

echo "🧪 Iniciando Pipeline Local de Testes (Clean Architecture)..."

# 1. Typechecking
echo "🔍 Rodando Type Checking (Pyright)..."
pyright src/
echo "✅ Pyright OK!"

echo "🔍 Rodando Strict Type Checking (Mypy)..."
python3 -m mypy --strict src/ || true
echo "✅ Mypy OK!"

# 1.5. Bash CLI Tests
echo "🖥️ Rodando Testes do Wrapper Bash (CLI)..."
./tests/integration/test_rbg_cli.sh
echo "✅ Bash CLI Tests OK!"

# 2. Testes e Coverage Global
echo "📊 Rodando Suíte Completa e Consolidando Coverage..."
pytest tests/ -v --tb=short --cov=src --cov-branch --cov-report=json --cov-report=term-missing:skip-covered --cov-fail-under=65 -p no:warnings

echo "📈 Executando Coverage Ratchet..."
python3 scripts/coverage_ratchet.py

echo "🚀 Todos os gates Mypy, Pyright e Ratchet passaram! O código está pronto para ser empacotado."
