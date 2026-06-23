#!/bin/bash
# Pipeline Reference: .agents/workflows/pipeline.md
#
# Script de configuração inicial (Onboarding)
# Instala os githooks locais no repositório.

set -euo pipefail

# Garante que roda a partir do diretório onde está, mas aponta para a raiz
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

HOOKS_SRC="$ROOT_DIR/packaging/git-hooks"
HOOKS_DEST="$ROOT_DIR/.git/hooks"

echo "⚙️ Configurando ambiente de desenvolvimento..."

# Verifica se a pasta .git existe
if [[ ! -d "$ROOT_DIR/.git" ]]; then
    echo "❌ Erro: Diretório .git não encontrado. O setup de hooks requer um repositório git."
    exit 1
fi

# Cria diretório de hooks se não existir
mkdir -p "$HOOKS_DEST"

# Copia e aplica permissões
for hook in commit-msg pre-push; do
    if [[ -f "$HOOKS_SRC/$hook" ]]; then
        echo "   -> Instalando hook: $hook"
        cp "$HOOKS_SRC/$hook" "$HOOKS_DEST/$hook"
        chmod +x "$HOOKS_DEST/$hook"
    else
        echo "❌ Erro: Template do hook '$hook' não encontrado em $HOOKS_SRC."
        exit 1
    fi
done

echo "✅ Git hooks configurados com sucesso em .git/hooks/"
