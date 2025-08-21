"""
Configuration de l'application Network Drive Mounter.
"""
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
RESOURCES_DIR = ROOT_DIR / 'resources'

# Configuration de l'application
APP_NAME = "Network Drive Mounter"
APP_VERSION = "1.0.0"
DEFAULT_WINDOW_SIZE = "600x600"
MIN_WINDOW_SIZE = (550, 550)

# Configuration des partages réseau
DEFAULT_FILESYSTEM = "cifs"
DEFAULT_OPTIONS = "rw,user"

# Chemins système
FSTAB_PATH = "/etc/fstab"
CREDENTIALS_DIR = "~/.cifs_credentials"

# Messages
MESSAGES = {
    "mount_success": "Partage monté avec succès sur {}",
    "mount_failed": "Échec du montage: {}",
    "fstab_updated": "Configuration ajoutée à fstab",
    "fstab_failed": "Échec de la mise à jour de fstab: {}",
    "missing_fields": "Veuillez remplir tous les champs obligatoires",
}
