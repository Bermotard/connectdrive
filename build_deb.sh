#!/bin/bash
# =============================================================================
#  build_deb.sh — Construit le paquet Debian/Ubuntu (Linux Mint) installable.
#
#  Usage : ./build_deb.sh
#  Sortie : dist/connectdrive_<version>_all.deb
#  Installation : sudo apt install ./dist/connectdrive_<version>_all.deb
# =============================================================================
set -euo pipefail

VERSION="1.1.0"
PKG="connectdrive"
ARCH="all"
FULL_VERSION="${VERSION}-1"
PKG_NAME="${PKG}_${FULL_VERSION}_${ARCH}"
STAGING="build/deb/${PKG_NAME}"

echo "==> Préparation du paquet ${PKG_NAME}"

# Nettoyage des builds précédents
rm -rf build/deb dist
mkdir -p build/deb dist

# Copie du squelette de packaging
cp -r packaging/deb "${STAGING}"

# Copie du code source (sans les __pycache__)
mkdir -p "${STAGING}/usr/share/connectdrive"
cp -r src "${STAGING}/usr/share/connectdrive/src"
find "${STAGING}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${STAGING}" -type f -name "*.pyc" -delete

# Documentation
cp README.md "${STAGING}/usr/share/doc/connectdrive/README.md"

# Permissions
chmod 755 "${STAGING}/usr/bin/connectdrive"
chmod 644 "${STAGING}/DEBIAN/control"
chmod 644 "${STAGING}/usr/share/applications/connectdrive.desktop"
chmod 644 "${STAGING}/usr/share/doc/connectdrive/copyright"
chmod 644 "${STAGING}/usr/share/icons/hicolor/scalable/apps/connectdrive.svg"

# Construction du paquet (propriétaire root:root)
echo "==> Construction du paquet avec dpkg-deb"
dpkg-deb --build --root-owner-group "${STAGING}" "dist/${PKG_NAME}.deb"

# Validation
echo "==> Validation du paquet"
dpkg-deb --info "dist/${PKG_NAME}.deb" | head -20
echo
echo "==> Contenu (aperçu)"
dpkg-deb --contents "dist/${PKG_NAME}.deb" | grep -E "(usr/bin/|applications/|icons/|DEBIAN/control|src/main.py)" | head -20

echo
echo "✅ Paquet créé : dist/${PKG_NAME}.deb"
echo "   Installation : sudo apt install ./dist/${PKG_NAME}.deb"
