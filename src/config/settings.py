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
DEFAULT_WINDOW_SIZE = "800x800"
MIN_WINDOW_SIZE = (700, 700)

# Configuration des partages réseau
DEFAULT_FILESYSTEM = "cifs"
DEFAULT_OPTIONS = "rw,user,file_mode=0777,dir_mode=0777"

# System paths
FSTAB_PATH = "/etc/fstab"
CREDENTIALS_DIR = "~/.cifs_credentials"

# Messages
MESSAGES = {
    "mount_success": "Share successfully mounted on {}",
    "mount_failed": "Mount failed: {}",
    "fstab_updated": "Configuration added to fstab",
    "fstab_failed": "Failed to update fstab: {}",
    "missing_fields": "Please fill in all required fields",
}
