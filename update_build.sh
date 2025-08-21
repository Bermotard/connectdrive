#!/bin/bash

# Vérifie si le fichier build.sh existe déjà
if [ -f "build.sh" ]; then
    echo "⚠️  Le fichier build.sh existe déjà. Il va être écrasé."
    read -p "Voulez-vous continuer ? (o/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        echo "Annulation."
        exit 1
    fi
fi

# Crée le contenu du fichier build.sh
cat > build.sh << 'EOL'
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
EOL

# Rendre le script exécutable
chmod +x build.sh

echo "✅ Le fichier build.sh a été régénéré avec succès !"
