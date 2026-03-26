#!/bin/bash
set -e

PKG_NAME="rgb-control"
VERSION="1.0.5"
REV="1"
ARCH="all"
DEB_DIR="${PKG_NAME}_${VERSION}-${REV}_${ARCH}"

echo "Building Debian package: $DEB_DIR"

# Clean up previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/scalable/apps"
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

# Copy source python package
cp -r rgb_control "$DEB_DIR/usr/share/$PKG_NAME/"

# Copy assets
cp "logo.svg" "$DEB_DIR/usr/share/$PKG_NAME/"
cp "544bd05c31a56c8347682a790975c619.gif" "$DEB_DIR/usr/share/$PKG_NAME/"
cp "rbg.sh" "$DEB_DIR/usr/bin/rbg.sh"
chmod +x "$DEB_DIR/usr/bin/rbg.sh"

# Create /usr/bin/rgb-control wrapper
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

# Copy Icon
cp "logo.svg" "$DEB_DIR/usr/share/icons/hicolor/scalable/apps/rgb-control.svg"

# Build .deb
echo "Running dpkg-deb --build..."
dpkg-deb --build "$DEB_DIR"

echo "Package $DEB_DIR.deb created successfully!"
