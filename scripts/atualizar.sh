#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

./build_deb.sh
VERSION=$(grep -m 1 '^version\s*=\s*"' pyproject.toml | cut -d '"' -f 2)
PACKAGE="$ROOT/builds/rgb-control_${VERSION}-1_all.deb"

if [ ! -f "$PACKAGE" ]; then
    echo "❌ Pacote não encontrado: $PACKAGE"
    exit 1
fi

sudo dpkg -i "$PACKAGE"
sudo apt-get install -f
