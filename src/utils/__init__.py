"""
Utilitaires pour l'application NetworkMounter.
"""

from .exceptions import (
    NetworkMounterError,
    MountError,
    UnmountError,
    FstabError,
    CredentialsError,
    ValidationError
)

from .validators import (
    validate_hostname,
    validate_share_path,
    validate_mount_point,
    validate_credentials,
    validate_fs_type
)

from .system import (
    run_command,
    ensure_directory,
    is_mounted,
    get_mounted_shares,
    secure_file_write,
    mount_share,
    unmount_share
)

from .fstab import Fstab, FstabEntry
from .credentials import CredentialsManager
from .logger import setup_logger, get_logger

__all__ = [
    # Exceptions
    'NetworkMounterError',
    'MountError',
    'UnmountError',
    'FstabError',
    'CredentialsError',
    'ValidationError',
    
    # Validators
    'validate_hostname',
    'validate_share_path',
    'validate_mount_point',
    'validate_credentials',
    'validate_fs_type',
    
    # System utilities
    'run_command',
    'ensure_directory',
    'is_mounted',
    'get_mounted_shares',
    'secure_file_write',
    'mount_share',
    'unmount_share',
    
    # Fstab
    'Fstab',
    'FstabEntry',
    
    # Credentials
    'CredentialsManager',
    
    # Logger
    'setup_logger',
    'get_logger'
]
