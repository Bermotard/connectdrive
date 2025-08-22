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
  src/main.py

# Vérifier si la compilation a réussi
if [ $? -eq 0 ]; then
    # Rendre l'exécutable... exécutable
    chmod +x dist/NetworkMounter
    echo "✅ Build terminé avec succès ! L'exécutable se trouve dans le dossier 'dist/'"
    echo "   Vous pouvez l'exécuter avec: ./dist/NetworkMounter"
else
    echo "❌ Erreur lors de la compilation. Vérifiez les messages d'erreur ci-dessus."
    exit 1
fi
