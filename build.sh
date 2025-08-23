#!/bin/bash

# Activer l'environnement virtuel
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Le dossier venv n'existe pas. Création d'un nouvel environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
fi

# Installer les dépendances
pip install -r requirements.txt

# Installer PyInstaller si nécessaire
pip install pyinstaller

# Nettoyer les builds précédents
rm -rf build dist

# Créer le dossier de sortie s'il n'existe pas
mkdir -p dist

# Créer l'exécutable avec la structure du projet
pyinstaller \
  --name NetworkMounter \
  --onefile \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "version.txt:." \
  --add-data "src/config:config" \
  --add-data "src/gui:gui" \
  --add-data "src/services:services" \
  --add-data "src/utils:utils" \
  --hidden-import "PyQt5.QtWidgets" \
  --hidden-import "PyQt5.QtCore" \
  --hidden-import "PyQt5.QtGui" \
  --hidden-import "cryptography" \
  --hidden-import "keyring" \
  --add-binary "/lib/x86_64-linux-gnu/libc.so.6:." \
  --add-binary "/lib/x86_64-linux-gnu/libm.so.6:." \
  src/__main__.py

# Check if compilation was successful
if [ $? -eq 0 ]; then
    # Make the executable... executable
    chmod +x dist/NetworkMounter
    echo "✅ Build completed successfully! The executable is in the 'dist/' folder"
    echo "   You can run it with: ./dist/NetworkMounter"
else
    echo "❌ Error during compilation. Please check the error messages above."
    exit 1
fi
