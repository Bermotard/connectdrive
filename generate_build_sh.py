#!/usr/bin/env python3
"""
Script pour générer ou mettre à jour le fichier build.sh
"""

def generate_build_sh():
    """Génère le contenu du fichier build.sh"""
    content = '''#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Clean previous builds
rm -rf build dist

# Create the executable
pyinstaller \
  --name NetworkMounter \
  --onefile \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "version.txt:." \
  network_mounter.py

# Make the executable executable
chmod +x dist/NetworkMounter

echo "Build complete! The executable is in the 'dist' directory."
'''
    return content

def main():
    """Fonction principale"""
    try:
        with open('build.sh', 'w', encoding='utf-8') as f:
            f.write(generate_build_sh())
        print("✅ Fichier build.sh généré avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors de la génération du fichier: {e}")

if __name__ == "__main__":
    main()
