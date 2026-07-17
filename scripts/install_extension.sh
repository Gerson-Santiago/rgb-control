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

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

echo -e "\n${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  ✅  Extensão GNOME instalada com sucesso!   ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${BOLD}  Próximas etapas:${RESET}\n"
echo -e "  ${CYAN}Passo 3${RESET} — Verificação manual do comportamento no sistema."
echo -e "  ${DIM}  Abra o painel GNOME e confirme que a extensão está ativa.${RESET}"
echo -e "  ${DIM}  Se o ícone não aparecer: Alt+F2 → r (ou faça logout/login).${RESET}"
echo -e "\n  ${CYAN}Passo 4${RESET} — Se tudo estiver OK, faça o commit:"
echo -e "  ${DIM}  \$ git add -A${RESET}"
echo -e "  ${DIM}  \$ git commit -m \"tipo(escopo): descrição\"  ${DIM}# Conventional Commits${RESET}"
echo -e "  ${DIM}  \$ git push origin <sua-branch>${RESET}"
echo -e "\n  ${YELLOW}⚠${RESET}  Se a verificação manual falhar, reverta com:"
echo -e "  ${DIM}  \$ git checkout -- .${RESET}"
echo ""
