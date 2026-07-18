#!/bin/bash
# Pipeline Reference: .agents/workflows/pipeline.md
# Version: 3.0.0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/shell_ui.sh
source "$ROOT/scripts/lib/shell_ui.sh"

VERSION=$(grep -m 1 '^version\s*=\s*"' pyproject.toml | cut -d '"' -f 2)
REV=$(grep -m 1 '^REV=' build_deb.sh | cut -d '=' -f 2 | tr -d '"')
PACKAGE="$ROOT/builds/rgb-control_${VERSION}-${REV}_all.deb"

if [ ! -f "$PACKAGE" ]; then
    echo "❌ Pacote não encontrado: $PACKAGE"
    echo "   Execute primeiro: bash scripts/pipeline_run.sh"
    exit 1
fi

sudo dpkg -i "$PACKAGE"
sudo apt-get install -f

echo "🔄 Atualizando caches do sistema..."
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
sudo update-desktop-database -q || true
if command -v appstreamcli > /dev/null 2>&1; then
    sudo appstreamcli update || sudo appstreamcli refresh-cache --force || true
fi

ui_banner "✅  Instalação concluída: v${VERSION}-${REV}"
ui_next_steps 2
