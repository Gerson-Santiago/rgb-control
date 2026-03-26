#!/bin/bash

# ==============================================================================
# OpenRGB Unified Controller
# ==============================================================================

PROJECT_DIR="/home/sant/Área de trabalho/PROJETOS/openrbg"
COLOR_GUM="#00f2ea"
DEVICE_ID=0

# Cores Predefinidas
declare -A COLORS
COLORS=(
    ["branco"]="FFFFFF"
    ["white"]="FFFFFF"
    ["preto"]="000000"
    ["black"]="000000"
    ["off"]="000000"
    ["vermelho"]="FF0000"
    ["red"]="FF0000"
    ["verde"]="00FF00"
    ["green"]="00FF00"
    ["azul"]="0000FF"
    ["blue"]="0000FF"
    ["amarelo"]="FFFF00"
    ["yellow"]="FFFF00"
    ["laranja"]="FF5500"
    ["orange"]="FF5500"
    ["ambar"]="FFB200"
    ["amber"]="FFB200"
    ["roxo"]="AA00FF"
    ["purple"]="AA00FF"
    ["ciano"]="00F2EA"
    ["cyan"]="00F2EA"
)

# Função para validar HEX
validate_hex() {
    local hex=$1
    if [[ $hex =~ ^#?([A-Fa-f0-9]{6})$ ]]; then
        return 0
    else
        return 1
    fi
}

# Função para aplicar a cor
apply_color() {
    local color=$1
    local name=$2
    
    # Remove # se estiver presente
    color=${color#\#}
    
    # Validação
    if ! validate_hex "$color" ; then
        echo -e "\033[31m❌ Erro: '#$color' não é válido (use 6 dígitos, ex: FF5500).\033[0m"
        return 1
    fi
    
    if openrgb --device $DEVICE_ID --mode static --color "$color" >/dev/null 2>&1 || \
       sudo openrgb --device $DEVICE_ID --mode static --color "$color" >/dev/null 2>&1; then
        echo -e "\033[32m✅ ${name:-#$color}\033[0m"
    else
        echo -e "\033[31m❌ Falha ao aplicar cor.\033[0m"
    fi
}

# Função do Menu Interativo (Gum)
run_menu() {
    echo "Escolha a cor dos LEDs:"
    local choice=$(gum choose --cursor.foreground="$COLOR_GUM" \
        "Branco" \
        "Amarelo" \
        "Laranja" \
        "Ambar" \
        "Roxo" \
        "Ciano" \
        "Vermelho" \
        "Verde" \
        "Azul" \
        "Desligar (Preto)" \
        "Personalizado (Hex)")

    case $choice in
        "Branco") apply_color "${COLORS[branco]}" "Branco" ;;
        "Amarelo") apply_color "${COLORS[amarelo]}" "Amarelo" ;;
        "Laranja") apply_color "${COLORS[laranja]}" "Laranja" ;;
        "Ambar") apply_color "${COLORS[ambar]}" "Ambar" ;;
        "Roxo") apply_color "${COLORS[roxo]}" "Roxo" ;;
        "Ciano") apply_color "${COLORS[ciano]}" "Ciano" ;;
        "Vermelho") apply_color "${COLORS[vermelho]}" "Vermelho" ;;
        "Verde") apply_color "${COLORS[verde]}" "Verde" ;;
        "Azul") apply_color "${COLORS[azul]}" "Azul" ;;
        "Desligar (Preto)") apply_color "${COLORS[preto]}" "Preto/OFF" ;;
        "Personalizado (Hex)")
            local hex=$(gum input --placeholder "Ex: FF5500" --prompt "Hex: #")
            if [[ -n $hex ]]; then
                apply_color "$hex"
            fi
            ;;
    esac
}

# Lógica Principal
if [[ $# -eq 0 ]]; then
    # Se não houver argumentos, abre o menu
    run_menu
else
    # Se houver argumento, verifica se é uma cor predefinida
    ARG=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    if [[ ${COLORS[$ARG]} ]]; then
        apply_color "${COLORS[$ARG]}" "$ARG"
    else
        # Caso contrário, assume que é um código HEX
        apply_color "$1" "Custom"
    fi
fi
