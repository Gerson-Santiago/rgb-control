#!/bin/bash
# Pipeline Reference: .agents/workflows/pipeline.md
set -e

UUID="rgb-control@sant.github.com"
EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$UUID"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ">> Removendo instalação antiga se houver..."
rm -rf "$EXT_DIR"

echo ">> Criando diretório da extensão..."
mkdir -p "$EXT_DIR"

echo ">> Copiando arquivos da extensão para o diretório local..."
cp -r "$SRC_DIR/gnome-extension/"* "$EXT_DIR/"

echo ">> Habilitando a extensão..."
if command -v gnome-extensions &> /dev/null; then
    gnome-extensions enable "$UUID" || {
        echo "⚠️  Aviso: Não foi possível habilitar a extensão '$UUID' automaticamente."
        echo "Você pode precisar reiniciar o GNOME Shell (Alt+F2, r ou fazer logout) e ativá-la no aplicativo 'Extensions' ou 'Extension Manager'."
    }
else
    echo "⚠️  Comando 'gnome-extensions' não encontrado. Ative a extensão manualmente."
fi

echo "✅ Extensão instalada localmente em: $EXT_DIR"
