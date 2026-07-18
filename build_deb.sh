#!/bin/bash
# Pipeline Reference: .agents/workflows/pipeline.md
set -e

PKG_NAME="rgb-control"
VERSION=$(grep -m 1 "^version = " pyproject.toml | cut -d '"' -f 2)
REV="1"
ARCH="all"
DEB_DIR="builds/${PKG_NAME}_${VERSION}-${REV}_${ARCH}"

echo ">> Executando Pipeline de Qualidade (Clean Architecture) <<"
./run_tests.sh

echo "Building Debian package: $DEB_DIR"

# Clean up previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/$PKG_NAME/assets"
mkdir -p "$DEB_DIR/usr/share/gnome-shell/extensions/rgb-control@sant.github.com"

# Create DEBIAN/control
cat <<EOF > "$DEB_DIR/DEBIAN/control"
Package: $PKG_NAME
Version: $VERSION-$REV
Section: utils
Priority: optional
Architecture: $ARCH
Depends: openrgb, python3
Maintainer: Sant <sant@local>
Description: Extensão GNOME Shell + CLI para controle de iluminação OpenRGB.
 Painel de acesso rápido no Shell com 8 cores configuráveis e CLI rico (rgb).
EOF

# Create DEBIAN/postinst
cat <<EOF > "$DEB_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if [ "\$1" = "configure" ]; then
    # Recarrega extensões do GNOME Shell se estiver rodando em sessão gráfica
    if command -v gnome-extensions > /dev/null 2>&1; then
        gnome-extensions enable rgb-control@sant.github.com 2>/dev/null || true
    fi
fi
EOF
chmod +x "$DEB_DIR/DEBIAN/postinst"

# Create DEBIAN/postrm
cat <<EOF > "$DEB_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "\$1" = "remove" ] || [ "\$1" = "purge" ]; then
    if command -v gnome-extensions > /dev/null 2>&1; then
        gnome-extensions disable rgb-control@sant.github.com 2>/dev/null || true
    fi
fi
EOF
chmod +x "$DEB_DIR/DEBIAN/postrm"

# Copia o módulo Python de configuração (rgb_config — puro, sem GTK)
cp -r src/rgb_config "$DEB_DIR/usr/share/$PKG_NAME/"

# Copia o SSOT de cores padrão
cp assets/default_config.json "$DEB_DIR/usr/share/$PKG_NAME/assets/"

# Copia o script CLI rgb.sh
cp "packaging/rgb.sh" "$DEB_DIR/usr/bin/rgb.sh"
chmod +x "$DEB_DIR/usr/bin/rgb.sh"

# Copia a extensão GNOME Shell
cp -r gnome-extension/* "$DEB_DIR/usr/share/gnome-shell/extensions/rgb-control@sant.github.com/"

# Build .deb
echo "Running dpkg-deb --build..."
dpkg-deb --build "$DEB_DIR"

echo "Package $DEB_DIR.deb created successfully!"

# Atualiza automaticamente o README.md com o nome correto do pacote (.deb) gerado nesta build
python3 -c "
import re
readme_path = 'README.md'
readme = open(readme_path, 'r', encoding='utf-8').read()
updated = re.sub(r'rgb-control_\d+\.\d+\.\d+-\d+_all\.deb', 'rgb-control_${VERSION}-${REV}_all.deb', readme)
open(readme_path, 'w', encoding='utf-8').write(updated)
"

# Limpeza de builds antigos: manter apenas a versão atual e as 3 versões anteriores mais recentes
echo ">> Limpando builds antigos (mantendo a atual e até 3 anteriores) <<"
for deb in $(ls builds/${PKG_NAME}_*.deb 2>/dev/null | sort -V | head -n -4); do
    echo "Removendo build antigo: $deb e seu diretório correspondente..."
    rm -f "$deb"
    rm -rf "${deb%.deb}"
done
