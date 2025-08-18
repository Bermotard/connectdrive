# ConnectDrive

Un projet Python pour gérer des connexions et des opérations de stockage.

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/bermotard/connectdrive.git
cd connectdrive
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
# .\venv\Scripts\activate  # Sur Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

### Monteur de lecteur réseau

Le programme `network_mounter.py` fournit une interface graphique pour monter des partages réseau et les ajouter au fichier fstab.

#### Prérequis

- Python 3.6 ou supérieur
- Paquets système requis (pour Ubuntu/Debian) :
  ```bash
  sudo apt-get install cifs-utils nfs-common
  ```

#### Installation des dépendances Python

```bash
pip install -r requirements.txt
```

#### Lancement du programme

```bash
python network_mounter.py
```

#### Fonctionnalités

1. **Monter un partage réseau** : Permet de monter un partage réseau immédiatement
2. **Ajouter à fstab** : Ajoute une entrée dans /etc/fstab pour un montage automatique au démarrage
3. **Tout faire** : Monte le partage et l'ajoute à fstab en une seule opération

#### Paramètres

- **Serveur** : L'adresse IP ou le nom d'hôte du serveur
- **Partage** : Le nom du partage réseau
- **Point de montage** : Le répertoire local où le partage sera monté
- **Utilisateur** : Le nom d'utilisateur pour l'authentification
- **Mot de passe** : Le mot de passe pour l'authentification
- **Domaine** : Le domaine (optionnel) pour l'authentification
- **Type de système de fichiers** : CIFS (Samba) ou NFS
- **Options** : Options de montage supplémentaires (séparées par des virgules)

#### Exemple d'utilisation

1. Entrez les détails de connexion du serveur
2. Cliquez sur "Monter" pour monter le partage immédiatement
3. Si le montage réussit, cliquez sur "Ajouter à fstab" pour le rendre permanent
4. Ou utilisez "Tout faire" pour effectuer les deux opérations en une fois

## Structure du projet

```
connectdrive/
├── src/           # Code source du projet
├── tests/         # Tests unitaires
├── docs/          # Documentation
├── .gitignore
├── README.md
└── requirements.txt
```
