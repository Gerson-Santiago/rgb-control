#!/usr/bin/env bash
# Pipeline Reference: .agents/workflows/pipeline.md
#
# Uso: Execute a partir da raiz do projeto:
#   bash scripts/pipeline_run.sh
#
# Este script NÃO deve ser chamado por outros scripts.
# É um wrapper interativo exclusivo para o operador humano.

set -euo pipefail

# ─── Verificação de contexto ──────────────────────────────────────────────────
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=scripts/lib/shell_ui.sh
source "$ROOT/scripts/lib/shell_ui.sh"

# BLUE é exclusivo deste script (cabeçalhos de etapa)
BLUE='\033[0;34m'

if [[ ! -f "$ROOT/pyproject.toml" || ! -f "$ROOT/build_deb.sh" ]]; then
    echo -e "\n${FAIL} ${RED}Execute a partir da raiz do projeto:${RESET}"
    echo -e "   ${DIM}bash scripts/pipeline_run.sh${RESET}\n"
    exit 1
fi

cd "$ROOT"

# ─── Leitura do estado atual ──────────────────────────────────────────────────
CURRENT_VERSION=$(grep -m 1 '^version\s*=\s*"' pyproject.toml | cut -d '"' -f 2)
CURRENT_REV=$(grep -m 1 '^REV=' build_deb.sh | cut -d '=' -f 2 | tr -d '"')

# ─── Funções utilitárias ──────────────────────────────────────────────────────
step() { echo -e "\n${BOLD}${BLUE}[$1]${RESET} $2"; }
ok()   { echo -e "  ${OK} $1"; }
fail() { echo -e "  ${FAIL} ${RED}$1${RESET}"; }
warn() { echo -e "  ${WARN} ${YELLOW}$1${RESET}"; }
info() { echo -e "  ${ARROW} ${DIM}$1${RESET}"; }

separator() {
    echo -e "${DIM}────────────────────────────────────────────────────────────${RESET}"
}

# Exibe o comando de rollback e sai com erro
abort_with_rollback() {
    local scenario="$1"
    separator
    echo -e "${RED}${BOLD}Pipeline interrompido na etapa: $2${RESET}"
    echo -e "\n${WARN} ${BOLD}Para reverter as alterações feitas até aqui:${RESET}\n"

    if [[ "$scenario" == "B" ]]; then
        echo -e "  ${YELLOW}git checkout -- pyproject.toml docs/stack.md docs/TESTS.md \\"
        echo -e "    src/rgb_control/main.py packaging/rgb.sh README.md scripts/atualizar.sh${RESET}"
    elif [[ "$scenario" == "C" ]]; then
        echo -e "  ${YELLOW}git checkout -- build_deb.sh README.md${RESET}"
    fi

    echo -e "  ${YELLOW}rm -rf builds/*${RESET}"
    echo -e "\n${DIM}Após o rollback, rode novamente: bash scripts/pipeline_run.sh${RESET}\n"
    exit 1
}

# Executa um comando em streaming; aborta com rollback se falhar
run_step() {
    local label="$1"
    local scenario="$2"
    shift 2

    echo -e "  ${ARROW} Executando: $label..."
    separator
    if ! "$@"; then
        separator
        fail "$label falhou!"
        abort_with_rollback "$scenario" "$label"
    fi
    separator
    ok "$label concluído com sucesso."
}

# Valida o formato de versão semântica X.Y.Z
validate_semver() {
    if [[ ! "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        fail "Formato inválido. Use X.Y.Z (ex: 1.2.3)"
        return 1
    fi
    return 0
}

# Aguarda confirmação do operador (Y/n)
confirm() {
    local prompt="$1"
    local answer
    while true; do
        echo -ne "\n  ${CYAN}?${RESET} $prompt ${DIM}[Y/n]${RESET} "
        read -r answer
        answer="${answer:-Y}"
        case "$answer" in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo -e "  ${WARN} Responda Y ou N." ;;
        esac
    done
}

# ─── Cabeçalho ────────────────────────────────────────────────────────────────
clear || true
echo -e "${BOLD}${BLUE}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║         OpenRGB — Pipeline de Desenvolvimento       ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  Estado atual do repositório:"
echo -e "  ${ARROW} Versão:  ${BOLD}$CURRENT_VERSION${RESET}"
echo -e "  ${ARROW} REV deb: ${BOLD}$CURRENT_REV${RESET}"
separator

# ─── Escolha do cenário ───────────────────────────────────────────────────────
echo -e "${BOLD}  Qual é o tipo de alteração?${RESET}\n"
echo -e "  ${CYAN}A${RESET}  Correção ou feature pontual ${DIM}(mesma versão)${RESET}"
echo -e "  ${CYAN}B${RESET}  Lançar nova versão semântica ${DIM}(bump X.Y.Z)${RESET}"
echo -e "  ${CYAN}C${RESET}  Alterar apenas o empacotamento Debian ${DIM}(novo REV)${RESET}"
echo -e "  ${CYAN}Q${RESET}  Sair\n"

SCENARIO=""
while [[ -z "$SCENARIO" ]]; do
    echo -ne "  ${CYAN}?${RESET} Escolha [A/B/C/Q]: "
    read -r choice
    case "${choice^^}" in
        A) SCENARIO="A" ;;
        B) SCENARIO="B" ;;
        C) SCENARIO="C" ;;
        Q) echo -e "\n  Pipeline cancelado.\n"; exit 0 ;;
        *) echo -e "  ${WARN} Opção inválida. Digite A, B, C ou Q." ;;
    esac
done

separator

# ─── Coleta de parâmetros específicos de cada cenário ────────────────────────
NEW_VERSION="$CURRENT_VERSION"
NEW_REV="$CURRENT_REV"

if [[ "$SCENARIO" == "B" ]]; then
    echo -e "${BOLD}  Cenário B — Nova versão semântica${RESET}"
    echo -e "  ${DIM}Versão atual: $CURRENT_VERSION${RESET}\n"

    while true; do
        echo -ne "  ${CYAN}?${RESET} Nova versão (formato X.Y.Z): "
        read -r NEW_VERSION
        if validate_semver "$NEW_VERSION"; then
            if [[ "$NEW_VERSION" == "$CURRENT_VERSION" ]]; then
                fail "A nova versão é igual à atual ($CURRENT_VERSION). Use o Cenário A para alterações sem bump."
            else
                ok "Versão válida: $CURRENT_VERSION → ${BOLD}$NEW_VERSION${RESET}"
                break
            fi
        fi
    done

elif [[ "$SCENARIO" == "C" ]]; then
    echo -e "${BOLD}  Cenário C — Revisão do empacotamento Debian${RESET}"
    echo -e "  ${DIM}REV atual: $CURRENT_REV — versão do código permanece $CURRENT_VERSION${RESET}\n"

    while true; do
        echo -ne "  ${CYAN}?${RESET} Novo REV (número inteiro): "
        read -r NEW_REV
        if [[ "$NEW_REV" =~ ^[0-9]+$ && "$NEW_REV" -gt 0 ]]; then
            if [[ "$NEW_REV" == "$CURRENT_REV" ]]; then
                fail "O novo REV é igual ao atual ($CURRENT_REV). Altere o valor em build_deb.sh manualmente e rode novamente."
            else
                ok "REV válido: $CURRENT_REV → ${BOLD}$NEW_REV${RESET}"
                break
            fi
        else
            fail "REV deve ser um número inteiro positivo."
        fi
    done
fi

# ─── Resumo e confirmação antes de executar ───────────────────────────────────
separator
echo -e "${BOLD}  Resumo do que será executado:${RESET}\n"

if [[ "$SCENARIO" == "A" ]]; then
    echo -e "  1. ${ARROW} ./run_tests.sh"
    echo -e "  2. ${ARROW} ./build_deb.sh  ${DIM}(gera rgb-control_${CURRENT_VERSION}-${CURRENT_REV}_all.deb)${RESET}"
    echo -e "\n  ${WARN} Etapas manuais após build:"
    echo -e "     3. ./scripts/atualizar.sh   ${DIM}(requer sudo)${RESET}"
    echo -e "     4. ./scripts/install_extension.sh"

elif [[ "$SCENARIO" == "B" ]]; then
    echo -e "  1. ${ARROW} python3 scripts/bump_version.py $NEW_VERSION"
    echo -e "  2. ${ARROW} ./run_tests.sh"
    echo -e "  3. ${ARROW} ./build_deb.sh  ${DIM}(gera rgb-control_${NEW_VERSION}-${CURRENT_REV}_all.deb)${RESET}"
    echo -e "\n  ${WARN} Etapas manuais após build:"
    echo -e "     4. ./scripts/atualizar.sh   ${DIM}(requer sudo)${RESET}"
    echo -e "     5. ./scripts/install_extension.sh"

elif [[ "$SCENARIO" == "C" ]]; then
    echo -e "  1. ${ARROW} Alterar REV=\"$CURRENT_REV\" → REV=\"$NEW_REV\" em build_deb.sh"
    echo -e "  2. ${ARROW} ./run_tests.sh"
    echo -e "  3. ${ARROW} ./build_deb.sh  ${DIM}(gera rgb-control_${CURRENT_VERSION}-${NEW_REV}_all.deb)${RESET}"
    echo -e "\n  ${WARN} Etapas manuais após build:"
    echo -e "     4. ./scripts/atualizar.sh   ${DIM}(requer sudo)${RESET}"
    echo -e "     5. ./scripts/install_extension.sh"
fi

if ! confirm "Confirmar e iniciar pipeline?"; then
    echo -e "\n  Pipeline cancelado.\n"
    exit 0
fi

separator

# ─── Execução do pipeline ─────────────────────────────────────────────────────

# Cenário B: bump de versão
if [[ "$SCENARIO" == "B" ]]; then
    step "1/3" "Bump de versão: $CURRENT_VERSION → $NEW_VERSION"
    run_step "Atualizando arquivos de versão" "B" \
        python3 scripts/bump_version.py "$NEW_VERSION"
fi

# Cenário C: atualização do REV no build_deb.sh
if [[ "$SCENARIO" == "C" ]]; then
    step "1/3" "Atualizando REV em build_deb.sh: $CURRENT_REV → $NEW_REV"
    if sed -i "s/^REV=\"$CURRENT_REV\"/REV=\"$NEW_REV\"/" build_deb.sh; then
        ok "REV atualizado em build_deb.sh"
    else
        fail "Falha ao atualizar REV em build_deb.sh"
        abort_with_rollback "C" "Atualização de REV"
    fi
fi

# Etapa de testes (todos os cenários)
STEP_TESTS="1/2"
[[ "$SCENARIO" != "A" ]] && STEP_TESTS="2/3"
step "$STEP_TESTS" "Executando suíte de testes (run_tests.sh)"
run_step "run_tests.sh" "$SCENARIO" bash run_tests.sh

# Build do pacote .deb (todos os cenários)
STEP_BUILD="2/2"
[[ "$SCENARIO" != "A" ]] && STEP_BUILD="3/3"
step "$STEP_BUILD" "Gerando pacote Debian (build_deb.sh)"
run_step "build_deb.sh" "$SCENARIO" bash build_deb.sh

# ─── Pós-build: orientação para etapas manuais ───────────────────────────────
separator

# Identifica o pacote gerado
BUILT_VERSION=$(grep -m 1 '^version\s*=\s*"' pyproject.toml | cut -d '"' -f 2)
BUILT_REV=$(grep -m 1 '^REV=' build_deb.sh | cut -d '=' -f 2 | tr -d '"')
PACKAGE_NAME="rgb-control_${BUILT_VERSION}-${BUILT_REV}_all.deb"

echo -e "${GREEN}${BOLD}  Build concluído com sucesso!${RESET}\n"
echo -e "  ${OK} Pacote gerado: ${BOLD}builds/$PACKAGE_NAME${RESET}\n"
echo -e "${BOLD}  Próximas etapas (manuais — requerem interação):${RESET}\n"
echo -e "  ${CYAN}Passo 1${RESET} — Instalar o pacote no sistema:"
echo -e "  ${DIM}  \$ bash scripts/atualizar.sh${RESET}"
echo -e "\n  ${CYAN}Passo 2${RESET} — Instalar a extensão GNOME:"
echo -e "  ${DIM}  \$ bash scripts/install_extension.sh${RESET}"
echo -e "\n  ${CYAN}Passo 3${RESET} — Verificação manual do comportamento no sistema."
echo -e "\n  ${CYAN}Passo 4${RESET} — Se tudo estiver OK, faça o commit:"
echo -e "  ${DIM}  \$ git add -A${RESET}"
echo -e "  ${DIM}  \$ git commit -m \"tipo(escopo): descrição\"  ${DIM}# Conventional Commits${RESET}"
echo -e "  ${DIM}  \$ git push origin <sua-branch>${RESET}"

separator

echo -e "  ${WARN} ${YELLOW}Se a verificação manual falhar, reverta com:${RESET}"
if [[ "$SCENARIO" == "B" ]]; then
    echo -e "  ${DIM}  git checkout -- pyproject.toml docs/stack.md docs/TESTS.md \\"
    echo -e "    src/rgb_control/main.py packaging/rgb.sh README.md scripts/atualizar.sh${RESET}"
elif [[ "$SCENARIO" == "C" ]]; then
    echo -e "  ${DIM}  git checkout -- build_deb.sh README.md${RESET}"
else
    echo -e "  ${DIM}  git checkout -- .   ${DIM}# sem alterações de versão para reverter${RESET}"
fi
echo -e "  ${DIM}  rm -rf builds/*${RESET}\n"
