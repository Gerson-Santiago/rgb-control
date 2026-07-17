#!/usr/bin/env bash
# Pipeline Reference: run_tests.sh / pipeline_run.sh
# scripts/lib/shell_ui.sh — Biblioteca compartilhada de UI para os scripts do RGB Control.
#
# Uso: source "$(dirname "${BASH_SOURCE[0]}")/lib/shell_ui.sh"
#
# Funções disponíveis:
#   ui_colors          — exporta as variáveis de cor (chamada automaticamente no source)
#   ui_banner TÍTULO   — imprime um banner colorido
#   ui_next_steps N    — imprime o bloco "Próximas etapas" a partir do passo N (1-4)

# ── Cores ─────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

OK="${GREEN}✓${RESET}"
FAIL="${RED}✗${RESET}"
WARN="${YELLOW}⚠${RESET}"
ARROW="${CYAN}→${RESET}"

# ── ui_banner ─────────────────────────────────────────────────────────────────
# Imprime um banner de sucesso com o título fornecido.
# Uso: ui_banner "✅  Instalação concluída: v1.0.1-1"
ui_banner() {
    local title="${1:-}"
    echo -e "\n${GREEN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════╗"
    printf "  ║  %-44s║\n" "$title"
    echo "  ╚══════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

# ── ui_next_steps ─────────────────────────────────────────────────────────────
# Imprime o bloco de "Próximas etapas" a partir do passo indicado.
# Uso: ui_next_steps <passo_inicial> [mensagem_rollback]
#
# Passos disponíveis:
#   1 — Instalar o pacote no sistema (bash scripts/atualizar.sh)
#   2 — Instalar a extensão GNOME    (bash scripts/install_extension.sh)
#   3 — Verificação manual
#   4 — git commit / push
#
# Exemplo:
#   ui_next_steps 2          → mostra passos 2, 3, 4 + rollback padrão
#   ui_next_steps 3          → mostra passos 3, 4 + rollback padrão
#   ui_next_steps 1 "git checkout -- pyproject.toml"
ui_next_steps() {
    local from="${1:-1}"
    local rollback="${2:-git checkout -- .}"

    echo -e "${BOLD}  Próximas etapas:${RESET}\n"

    if [[ "$from" -le 1 ]]; then
        echo -e "  ${CYAN}Passo 1${RESET} — Instalar o pacote no sistema:"
        echo -e "  ${DIM}  \$ bash scripts/atualizar.sh${RESET}\n"
    fi

    if [[ "$from" -le 2 ]]; then
        echo -e "  ${CYAN}Passo 2${RESET} — Instalar a extensão GNOME:"
        echo -e "  ${DIM}  \$ bash scripts/install_extension.sh${RESET}\n"
    fi

    if [[ "$from" -le 3 ]]; then
        echo -e "  ${CYAN}Passo 3${RESET} — Verificação manual do comportamento no sistema."
        echo -e "  ${DIM}  Abra o painel GNOME e confirme que a extensão está ativa.${RESET}"
        echo -e "  ${DIM}  Se o ícone não aparecer: Menu Desligar → Encerrar sessão...${RESET}\n"
    fi

    echo -e "  ${CYAN}Passo 4${RESET} — Se tudo estiver OK, faça o commit:"
    echo -e "  ${DIM}  \$ git add -A${RESET}"
    echo -e "  ${DIM}  \$ git commit -m \"tipo(escopo): descrição\"  ${DIM}# Conventional Commits${RESET}"
    echo -e "  ${DIM}  \$ git push origin <sua-branch>${RESET}"
    echo -e "\n  ${WARN}  Se a verificação manual falhar, reverta com:"
    echo -e "  ${DIM}  \$ ${rollback}${RESET}"
    echo ""
}
