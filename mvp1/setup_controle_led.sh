#!/bin/bash

# 🎨 Setup do Controle LED - Air Mouse LE-7278
# Script de instalação de dependências e configuração

set -e  # Sair se algum comando falhar

echo "========================================"
echo "🎨 SETUP - Controle LED com Air Mouse"
echo "========================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# 1. Verificar dependências do sistema
# ============================================================================

echo -e "${BLUE}[1/5]${NC} Verificando dependências do sistema..."

DEPS_MISSING=0

# evdev
if ! python3 -c "import evdev" 2>/dev/null; then
    echo -e "  ${YELLOW}⚠️  python3-evdev não encontrado${NC}"
    DEPS_MISSING=1
fi

# notify-send
if ! command -v notify-send &> /dev/null; then
    echo -e "  ${YELLOW}⚠️  libnotify-bin não encontrado${NC}"
    DEPS_MISSING=1
fi

# openrgb
if ! command -v openrgb &> /dev/null; then
    echo -e "  ${YELLOW}⚠️  openrgb não encontrado${NC}"
    DEPS_MISSING=1
fi

if [ $DEPS_MISSING -eq 0 ]; then
    echo -e "  ${GREEN}✅ Todas as dependências encontradas${NC}"
else
    echo -e "  ${YELLOW}Instalando dependências...${NC}"
    sudo apt update
    sudo apt install -y python3-evdev libnotify-bin
fi

echo ""

# ============================================================================
# 2. Configurar grupo input (sem sudo)
# ============================================================================

echo -e "${BLUE}[2/5]${NC} Configurando acesso ao grupo input..."

if groups $USER | grep -q input; then
    echo -e "  ${GREEN}✅ Usuário já está no grupo input${NC}"
else
    echo -e "  ${YELLOW}Adicionando usuário ao grupo input...${NC}"
    sudo usermod -aG input $USER
    echo -e "  ${YELLOW}⚠️  Você precisa fazer logout/login para aplicar!${NC}"
fi

echo ""

# ============================================================================
# 3. Copiar script para local apropriado
# ============================================================================

echo -e "${BLUE}[3/5]${NC} Instalando script controle_led.py..."

SCRIPT_DIR="/home/$USER/Área de trabalho/PROJETOS/openrgb"
SCRIPT_PATH="$SCRIPT_DIR/controle_led.py"

if [ ! -d "$SCRIPT_DIR" ]; then
    echo -e "  ${YELLOW}Criando diretório: $SCRIPT_DIR${NC}"
    mkdir -p "$SCRIPT_DIR"
fi

# Copia o script (assumindo que está no mesmo diretório)
if [ -f "./controle_led.py" ]; then
    cp ./controle_led.py "$SCRIPT_PATH"
    chmod +x "$SCRIPT_PATH"
    echo -e "  ${GREEN}✅ Script instalado em: $SCRIPT_PATH${NC}"
else
    echo -e "  ${RED}❌ controle_led.py não encontrado no diretório atual!${NC}"
    echo -e "     Copie manualmente para: $SCRIPT_PATH"
fi

echo ""

# ============================================================================
# 4. Criar alias no .bashrc
# ============================================================================

echo -e "${BLUE}[4/5]${NC} Configurando aliases..."

BASHRC="$HOME/.bashrc"

if grep -q "alias led-daemon" "$BASHRC"; then
    echo -e "  ${YELLOW}Alias led-daemon já existe em .bashrc${NC}"
else
    echo "" >> "$BASHRC"
    echo "# 🎨 Air Mouse LED Control" >> "$BASHRC"
    echo "alias led-daemon='python3 \"$SCRIPT_PATH\"'" >> "$BASHRC"
    echo "alias led-stop='pkill -f controle_led.py'" >> "$BASHRC"
    echo -e "  ${GREEN}✅ Aliases adicionados ao .bashrc${NC}"
    echo -e "     Use: ${YELLOW}led-daemon${NC} para iniciar"
    echo -e "     Use: ${YELLOW}led-stop${NC} para parar"
fi

echo ""

# ============================================================================
# 5. Criar systemd service (opcional)
# ============================================================================

echo -e "${BLUE}[5/5]${NC} Configurando systemd service (opcional)..."

SERVICE_FILE="/etc/systemd/system/air-mouse-leds.service"

cat > /tmp/air-mouse-leds.service << 'EOF'
[Unit]
Description=Air Mouse LED Control
Documentation=https://github.com/sant0s12/openrgb-air-mouse
After=graphical.target
Wants=graphical-session.service

[Service]
Type=simple
User=%USER%
ExecStart=/usr/bin/python3 %SCRIPT_PATH%
Restart=on-failure
RestartSec=5
Environment="DISPLAY=:0"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"

[Install]
WantedBy=graphical.target
EOF

# Substitui placeholders
sed -i "s|%USER%|$USER|g" /tmp/air-mouse-leds.service
sed -i "s|%SCRIPT_PATH%|$SCRIPT_PATH|g" /tmp/air-mouse-leds.service

echo ""
echo -e "  ${YELLOW}Para instalar como serviço automático:${NC}"
echo ""
echo -e "    ${BLUE}sudo cp /tmp/air-mouse-leds.service $SERVICE_FILE${NC}"
echo -e "    ${BLUE}sudo systemctl daemon-reload${NC}"
echo -e "    ${BLUE}sudo systemctl enable air-mouse-leds${NC}"
echo -e "    ${BLUE}sudo systemctl start air-mouse-leds${NC}"
echo ""

# ============================================================================
# RESUMO
# ============================================================================

echo ""
echo "========================================"
echo -e "${GREEN}✅ SETUP CONCLUÍDO!${NC}"
echo "========================================"
echo ""
echo "Próximos passos:"
echo ""
echo "1️⃣  Faça logout/login para aplicar grupo input:"
echo -e "   ${YELLOW}logout ou: exec su - $USER${NC}"
echo ""
echo "2️⃣  Conecte o Air Mouse LE-7278 na USB"
echo ""
echo "3️⃣  Inicie o daemon:"
echo -e "   ${YELLOW}led-daemon${NC}"
echo ""
echo "4️⃣  Teste os comandos:"
echo -e "   • Long press ${BLUE}OK${NC} (3s) → Ativar/Desativar MODO LED"
echo -e "   • ${BLUE}Vol+${NC} / ${BLUE}Vol-${NC} → Navegar cores"
echo -e "   • ${BLUE}Back${NC} → Desativar MODO LED"
echo ""
echo "5️⃣  Para parar o daemon:"
echo -e "   ${YELLOW}led-stop${NC}"
echo ""
