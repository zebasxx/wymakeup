#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-1.0.0}"
PACKAGE="wymakeup"
APPLICATION_ID="com.wymakeup.WayMakeup"
ARCHITECTURE="all"
BUILD_DIR="$ROOT_DIR/build/deb"
PACKAGE_DIR="$BUILD_DIR/${PACKAGE}_${VERSION}_${ARCHITECTURE}"
OUTPUT_DIR="$ROOT_DIR/dist"
DEB_PATH="$OUTPUT_DIR/${PACKAGE}_${VERSION}_${ARCHITECTURE}.deb"

rm -rf "$PACKAGE_DIR"
mkdir -p \
  "$PACKAGE_DIR/DEBIAN" \
  "$PACKAGE_DIR/usr/bin" \
  "$PACKAGE_DIR/usr/share/applications" \
  "$PACKAGE_DIR/usr/share/doc/$PACKAGE" \
  "$PACKAGE_DIR/usr/share/icons/hicolor/scalable/apps" \
  "$PACKAGE_DIR/usr/share/$PACKAGE"

install -m 0755 "$ROOT_DIR/app.py" "$PACKAGE_DIR/usr/share/$PACKAGE/app.py"
install -m 0644 "$ROOT_DIR/LICENSE" "$PACKAGE_DIR/usr/share/doc/$PACKAGE/copyright"
install -m 0644 "$ROOT_DIR/README.md" "$PACKAGE_DIR/usr/share/doc/$PACKAGE/README.md"
install -m 0644 "$ROOT_DIR/waymarkup.desktop" "$PACKAGE_DIR/usr/share/applications/$APPLICATION_ID.desktop"
install -m 0644 "$ROOT_DIR/assets/icons/$PACKAGE.svg" "$PACKAGE_DIR/usr/share/icons/hicolor/scalable/apps/$PACKAGE.svg"

cat > "$PACKAGE_DIR/usr/bin/$PACKAGE" <<'WRAPPER'
#!/usr/bin/env bash
exec python3 /usr/share/wymakeup/app.py "$@"
WRAPPER
chmod 0755 "$PACKAGE_DIR/usr/bin/$PACKAGE"

cat > "$PACKAGE_DIR/DEBIAN/control" <<CONTROL
Package: $PACKAGE
Version: $VERSION
Section: graphics
Priority: optional
Architecture: $ARCHITECTURE
Maintainer: WayMakeup Maintainers
Depends: python3, python3-gi, python3-cairo, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-pango-1.0, hicolor-icon-theme
Homepage: https://github.com/GitHubSeba/wymakeup
Description: Transparent fullscreen drawing window for Ubuntu Wayland
 WayMakeup opens a transparent GTK drawing window for sketching arrows,
 rectangles, circles, and text on top of the desktop before taking screenshots.
CONTROL

mkdir -p "$OUTPUT_DIR"
dpkg-deb --build --root-owner-group "$PACKAGE_DIR" "$DEB_PATH"

echo "Built $DEB_PATH"
echo "Install with: sudo apt install ./dist/${PACKAGE}_${VERSION}_${ARCHITECTURE}.deb"
