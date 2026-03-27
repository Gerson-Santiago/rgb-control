#!/bin/bash
set -e

PKG_NAME="rgb-control"
VERSION=$(grep -m 1 "^version = " pyproject.toml | cut -d '"' -f 2)
REV="1"
ARCH="all"
DEB_DIR="${PKG_NAME}_${VERSION}-${REV}_${ARCH}"

echo ">> Executando Pipeline de Qualidade (Clean Architecture) <<"
./run_tests.sh

echo "Building Debian package: $DEB_DIR"

# Clean up previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/usr/share/$PKG_NAME"

# Create DEBIAN/control
cat <<EOF > "$DEB_DIR/DEBIAN/control"
Package: $PKG_NAME
Version: $VERSION-$REV
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3, python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-adw-1
Maintainer: Sant <sant@local>
Description: Interface Gráfica moderna em GTK4 para controle do OpenRGB com integrações.
EOF

# Create DEBIAN/postinst (atualiza cache de ícones)
cat <<EOF > "$DEB_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if [ "\$1" = "configure" ]; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
    update-desktop-database -q || true
fi
EOF
chmod +x "$DEB_DIR/DEBIAN/postinst"

# Create DEBIAN/postrm (limpa cache)
cat <<EOF > "$DEB_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "\$1" = "remove" ] || [ "\$1" = "purge" ]; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
    update-desktop-database -q || true
fi
EOF
chmod +x "$DEB_DIR/DEBIAN/postrm"

# Copy source python packages
cp -r src/rgb_control "$DEB_DIR/usr/share/$PKG_NAME/"
cp -r src/rgb_daemon "$DEB_DIR/usr/share/$PKG_NAME/"

# Copy assets
cp -r assets "$DEB_DIR/usr/share/$PKG_NAME/"
cp "rbg.sh" "$DEB_DIR/usr/bin/rbg.sh"
chmod +x "$DEB_DIR/usr/bin/rbg.sh"

# Create /usr/bin/rgb-control wrapper (mesmo diretório para assets)
cat <<EOF > "$DEB_DIR/usr/bin/rgb-control"
#!/bin/bash
export PYTHONPATH="/usr/share/$PKG_NAME:\$PYTHONPATH"
exec python3 -m rgb_control.main "\$@"
EOF
chmod +x "$DEB_DIR/usr/bin/rgb-control"

# Create .desktop file
cat <<EOF > "$DEB_DIR/usr/share/applications/rgb-control.desktop"
[Desktop Entry]
Name=RGB Control
Comment=Controle de Iluminação OpenRGB
Exec=/usr/bin/rgb-control
Icon=rgb-control
Terminal=false
Type=Application
Categories=Utility;Settings;HardwareSettings;
Keywords=rgb;led;openrgb;color;lighting;
EOF

# Copy Icons - PNG (256x256)
cp "assets/logo.png" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/rgb-control.png"

# Build .deb
echo "Running dpkg-deb --build..."
dpkg-deb --build "$DEB_DIR"

echo "Package $DEB_DIR.deb created successfully!"
