#!/bin/bash
# run_tests.sh - Executado antes do build_deb.sh ou git push
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

echo "🧪 Iniciando Pipeline Local de Testes (Clean Architecture)..."

# 1. Typechecking
echo "🔍 Rodando Type Checking (Pyright)..."
pyright src/
echo "✅ Type Checking OK!"

# 2. Testes e Coverage Global
echo "📊 Rodando Suíte Completa e Consolidando Coverage..."
pytest tests/ -v --tb=short --cov=src --cov-report=term-missing:skip-covered --cov-fail-under=70 -p no:warnings

echo "🚀 Todos os testes passaram! O código está pronto para ser empacotado."
