#!/bin/bash
# Pipeline Reference: .agents/workflows/pipeline.md
# Version: 1.1.14
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

