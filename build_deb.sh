#!/bin/bash
set -e

PKG_NAME="rgb-control"
VERSION=$(grep -m 1 "^version = " pyproject.toml | cut -d '"' -f 2)
REV="1"
ARCH="all"
DEB_DIR="builds/${PKG_NAME}_${VERSION}-${REV}_${ARCH}"

# Grava a versão empacotada para que a GUI possa exibi-la na base (rodapé)
echo "v${VERSION}" > assets/version.txt

echo ">> Executando Pipeline de Qualidade (Clean Architecture) <<"
./run_tests.sh

echo "Building Debian package: $DEB_DIR"

# Clean up previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/usr/share/$PKG_NAME"
mkdir -p "$DEB_DIR/lib/systemd/system"
mkdir -p "$DEB_DIR/usr/share/gnome-shell/extensions/rgb-control@sant.github.com"

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

# Create DEBIAN/postinst (atualiza cache e ativa serviço daemon)
cat <<EOF > "$DEB_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if [ "\$1" = "configure" ]; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
    update-desktop-database -q || true
    systemctl daemon-reload || true
    systemctl enable rgb-control-daemon.service || true
    systemctl restart rgb-control-daemon.service || true
fi
EOF
chmod +x "$DEB_DIR/DEBIAN/postinst"

# Create DEBIAN/postrm (limpa cache e desativa serviço daemon)
cat <<EOF > "$DEB_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "\$1" = "remove" ] || [ "\$1" = "purge" ]; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
    update-desktop-database -q || true
    systemctl stop rgb-control-daemon.service || true
    systemctl disable rgb-control-daemon.service || true
    systemctl daemon-reload || true
fi
EOF
chmod +x "$DEB_DIR/DEBIAN/postrm"

# Copy source python packages
cp -r src/rgb_control "$DEB_DIR/usr/share/$PKG_NAME/"
cp -r src/rgb_daemon "$DEB_DIR/usr/share/$PKG_NAME/"

# Copy assets
cp -r assets "$DEB_DIR/usr/share/$PKG_NAME/"
cp "packaging/rgb.sh" "$DEB_DIR/usr/bin/rgb.sh"
chmod +x "$DEB_DIR/usr/bin/rgb.sh"

# Copy systemd service
cp "packaging/rgb-control-daemon.service" "$DEB_DIR/lib/systemd/system/rgb-control-daemon.service"

# Copy GNOME Shell extension
cp -r gnome-extension/* "$DEB_DIR/usr/share/gnome-shell/extensions/rgb-control@sant.github.com/"

# Create /usr/bin/rgb-control wrapper (mesmo diretório para assets)
cat <<EOF > "$DEB_DIR/usr/bin/rgb-control"
#!/bin/bash
export PYTHONPATH="/usr/share/$PKG_NAME:\$PYTHONPATH"
exec python3 -m rgb_control.main "\$@"
EOF
chmod +x "$DEB_DIR/usr/bin/rgb-control"

# Create .desktop file
cat <<EOF > "$DEB_DIR/usr/share/applications/com.github.sant.rgbcontrol.desktop"
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

# Copy Icons - SVG (Scalable) & PNG (256x256)
cp "assets/logo.svg" "$DEB_DIR/usr/share/icons/hicolor/scalable/apps/rgb-control.svg"
cp "assets/logo.png" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/rgb-control.png"

# Build .deb
echo "Running dpkg-deb --build..."
dpkg-deb --build "$DEB_DIR"

echo "Package $DEB_DIR.deb created successfully!"

# Limpeza de builds antigos: manter apenas a versão atual e as 3 versões anteriores mais recentes
echo ">> Limpando builds antigos (mantendo a atual e até 3 anteriores) <<"
for deb in $(ls builds/${PKG_NAME}_*.deb 2>/dev/null | sort -V | head -n -4); do
    echo "Removendo build antigo: $deb e seu diretório correspondente..."
    rm -f "$deb"
    rm -rf "${deb%.deb}"
done
