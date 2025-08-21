#!/bin/bash

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier si venv existe, sinon le créer
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install pyinstaller
else
    source venv/bin/activate
fi

# Installer les dépendances
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

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
if [ -f "dist/NetworkMounter" ]; then
    chmod +x dist/NetworkMounter
    echo "✅ Build réussi ! L'exécutable se trouve dans le dossier 'dist/'"
else
    echo "❌ La construction a échoué. Vérifiez les messages d'erreur ci-dessus."
    exit 1
fi
