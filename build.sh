#!/bin/bash

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Nettoyer les builds précédents
rm -rf build dist

# Créer l'exécutable
pyinstaller \
  --name NetworkMounter \
  --onefile \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "version.txt:." \
  network_mounter.py

# Rendre l'exécutable... exécutable
chmod +x dist/NetworkMounter

echo "✅ Build terminé ! L'exécutable se trouve dans le dossier 'dist/'"
