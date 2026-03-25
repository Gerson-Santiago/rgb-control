#!/bin/bash

# 🔍 Script de Diagnóstico - Controle LED com Air Mouse
# Testa todas as dependências e configurações

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "========================================"
echo -e "${BLUE}🔍 DIAGNÓSTICO - Controle LED${NC}"
echo "========================================"
echo ""

# ============================================================================
# 1. VERIFICAR DEPENDÊNCIAS
# ============================================================================

echo -e "${BLUE}[1/6]${NC} Verificando dependências..."
echo ""

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}✅${NC} $1: $(which $1)"
        return 0
    else
        echo -e "  ${RED}❌${NC} $1: não encontrado"
        return 1
    fi
}

check_python_module() {
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} Python módulo '$1': OK"
        return 0
    else
        echo -e "  ${RED}❌${NC} Python módulo '$1': não encontrado"
        return 1
    fi
}

check_command "python3"
check_command "openrgb"
check_command "notify-send"
echo ""
check_python_module "evdev"
echo ""

# ============================================================================
# 2. VERIFICAR GRUPO INPUT
# ============================================================================

echo -e "${BLUE}[2/6]${NC} Verificando grupo input..."
echo ""

if groups $USER | grep -q input; then
    echo -e "  ${GREEN}✅${NC} Usuário '$USER' está no grupo 'input'"
else
    echo -e "  ${RED}❌${NC} Usuário '$USER' NÃO está no grupo 'input'"
    echo -e "     Execute: ${YELLOW}sudo usermod -aG input $USER${NC}"
    echo -e "     E faça logout/login"
fi
echo ""

# ============================================================================
# 3. DESCOBRIR AIR MOUSE
# ============================================================================

echo -e "${BLUE}[3/6]${NC} Procurando Air Mouse LE-7278..."
echo ""

# Via lsusb
echo "  Dispositivos USB:"
if lsusb | grep -i "1915\|lelong\|2.4g" > /dev/null 2>&1; then
    lsusb | grep -i "1915\|lelong\|2.4g" | sed 's/^/    /'
    echo -e "  ${GREEN}✅${NC} Air Mouse detectado via USB"
else
    echo -e "  ${YELLOW}⚠️  Não encontrado via lsusb (pode estar desconectado)${NC}"
fi
echo ""

# Via /dev/input
echo "  Dispositivos de input:"
FOUND=0
for event in /dev/input/event*; do
    if [ -e "$event" ]; then
        NAME=$(cat /proc/bus/input/devices 2>/dev/null | grep -A1 "$event" | grep "N:" | cut -d= -f2 | tr -d '"' || echo "Unknown")
        if echo "$NAME" | grep -iq "xing\|lelong\|2.4g"; then
            echo -e "    ${GREEN}✅${NC} $event - $NAME"
            FOUND=1
        fi
    fi
done

if [ $FOUND -eq 0 ]; then
    echo -e "    ${YELLOW}⚠️  Nenhum Air Mouse encontrado em /dev/input/${NC}"
    echo ""
    echo "    Conecte o Air Mouse e tente novamente, ou use:"
    echo -e "      ${YELLOW}sudo evtest${NC}"
fi
echo ""

# ============================================================================
# 4. TESTAR OPENRGB
# ============================================================================

echo -e "${BLUE}[4/6]${NC} Testando OpenRGB..."
echo ""

if command -v openrgb &> /dev/null; then
    echo "  Listar devices:"
    if openrgb --list-devices 2>&1 | head -5; then
        echo ""
        echo -e "  ${GREEN}✅${NC} OpenRGB funcionando"
    else
        echo -e "  ${YELLOW}⚠️  OpenRGB respondeu, mas pode não ter devices${NC}"
    fi
else
    echo -e "  ${RED}❌${NC} OpenRGB não encontrado"
fi
echo ""

# ============================================================================
# 5. TESTAR NOTIFY-SEND
# ============================================================================

echo -e "${BLUE}[5/6]${NC} Testando notificações desktop..."
echo ""

if command -v notify-send &> /dev/null; then
    echo "  Enviando notificação de teste..."
    notify-send "🎨 Teste" "Se você viu esta notificação, tudo está OK!" \
        --icon=preferences-color --expire-time=3000
    echo -e "  ${GREEN}✅${NC} notify-send funcionando"
else
    echo -e "  ${RED}❌${NC} notify-send não encontrado"
fi
echo ""

# ============================================================================
# 6. VERIFICAR SCRIPT
# ============================================================================

echo -e "${BLUE}[6/6]${NC} Verificando script controle_led.py..."
echo ""

SCRIPT_PATHS=(
    "/home/$USER/Área de trabalho/PROJETOS/openrgb/controle_led.py"
    "./controle_led.py"
    "$HOME/controle_led.py"
)

SCRIPT_FOUND=0
for path in "${SCRIPT_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo -e "  ${GREEN}✅${NC} Script encontrado: $path"
        SCRIPT_FOUND=1
        
        # Verificar se é executável
        if [ -x "$path" ]; then
            echo -e "     ${GREEN}✅${NC} Arquivo é executável"
        else
            echo -e "     ${YELLOW}⚠️  Arquivo não é executável${NC}"
            echo -e "        Execute: ${YELLOW}chmod +x '$path'${NC}"
        fi
        break
    fi
done

if [ $SCRIPT_FOUND -eq 0 ]; then
    echo -e "  ${RED}❌${NC} Script não encontrado em nenhum local esperado"
fi
echo ""

# ============================================================================
# RESUMO
# ============================================================================

echo "========================================"
echo -e "${BLUE}📋 RESUMO DO DIAGNÓSTICO${NC}"
echo "========================================"
echo ""
echo "Para usar o daemon:"
echo ""
echo "1️⃣  Se houver erros acima, corrija-os:"
echo -e "   • Instale dependências: ${YELLOW}sudo apt install python3-evdev libnotify-bin${NC}"
echo -e "   • Adicione ao grupo input: ${YELLOW}sudo usermod -aG input \$USER${NC}"
echo -e "   • Faça logout/login"
echo ""
echo "2️⃣  Conecte o Air Mouse na USB"
echo ""
echo "3️⃣  Inicie o daemon:"
if [ $SCRIPT_FOUND -eq 1 ]; then
    echo -e "   ${YELLOW}python3 /home/$USER/Área de trabalho/PROJETOS/openrgb/controle_led.py${NC}"
else
    echo -e "   ${YELLOW}python3 /caminho/para/controle_led.py${NC}"
fi
echo ""
echo "4️⃣  Teste os botões:"
echo -e "   • Long press ${BLUE}OK${NC} (3s) → Ativar MODO LED"
echo -e "   • ${BLUE}Vol+${NC} / ${BLUE}Vol-${NC} → Navegar cores"
echo -e "   • ${BLUE}Back${NC} → Desativar MODO LED"
echo ""
echo "5️⃣  Ver logs em tempo real (se instalado como serviço):"
echo -e "   ${YELLOW}sudo journalctl -u air-mouse-leds -f${NC}"
echo ""
