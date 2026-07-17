#!/bin/bash
# Pipeline Reference: .agents/workflows/pipeline.md
# Version: 1.0.1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

./build_deb.sh
VERSION=$(grep -m 1 '^version\s*=\s*"' pyproject.toml | cut -d '"' -f 2)
REV=$(grep -m 1 '^REV=' build_deb.sh | cut -d '=' -f 2 | tr -d '"')
PACKAGE="$ROOT/builds/rgb-control_${VERSION}-${REV}_all.deb"

if [ ! -f "$PACKAGE" ]; then
    echo "❌ Pacote não encontrado: $PACKAGE"
    exit 1
fi

sudo dpkg -i "$PACKAGE"
sudo apt-get install -f

echo "🔄 Atualizando caches do sistema..."
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
sudo update-desktop-database -q || true
if command -v appstreamcli >/dev/null 2>&1; then
    sudo appstreamcli update || sudo appstreamcli refresh-cache --force || true
fi

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

echo -e "\n${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo -e "  ║  ✅  Instalação concluída: v${VERSION}-${REV}${RESET}${GREEN}${BOLD}"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${BOLD}  Próximas etapas:${RESET}\n"
echo -e "  ${CYAN}Passo 2${RESET} — Instalar a extensão GNOME:"
echo -e "  ${DIM}  \$ bash scripts/install_extension.sh${RESET}"
echo -e "\n  ${CYAN}Passo 3${RESET} — Verificação manual do comportamento no sistema."
echo -e "\n  ${CYAN}Passo 4${RESET} — Se tudo estiver OK, faça o commit:"
echo -e "  ${DIM}  \$ git add -A${RESET}"
echo -e "  ${DIM}  \$ git commit -m \"tipo(escopo): descrição\"  ${DIM}# Conventional Commits${RESET}"
echo -e "  ${DIM}  \$ git push origin <sua-branch>${RESET}"
echo -e "\n  ${YELLOW}⚠${RESET}  Se a verificação manual falhar, reverta com:"
echo -e "  ${DIM}  \$ git checkout -- .${RESET}"
echo ""
