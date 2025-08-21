"""
Validateurs pour les entrées utilisateur de l'application NetworkMounter.
"""
import re
import ipaddress
from typing import Optional, Tuple, Union
from pathlib import Path
from .exceptions import ValidationError

def validate_hostname(hostname: str) -> bool:
    """
    Valide un nom d'hôte ou une adresse IP.
    
    Args:
        hostname: Nom d'hôte ou adresse IP à valider
        
    Returns:
        bool: True si valide, False sinon
    """
    if not hostname:
        return False
    
    # Vérifier si c'est une adresse IP valide
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    
    # Vérifier si c'est un nom d'hôte valide
    if len(hostname) > 255:
        return False
    
    # Un nom d'hôte ne peut pas commencer ou finir par un point
    if hostname[-1] == "." or hostname[0] == ".":
        return False
    
    # Vérifier chaque partie du nom d'hôte
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def validate_share_path(share_path: str) -> bool:
    """
    Valide un chemin de partage réseau.
    
    Args:
        share_path: Chemin de partage à valider
        
    Returns:
        bool: True si valide, False sinon
    """
    if not share_path:
        return False
    
    # Vérifier le format de base (doit commencer par / et ne pas contenir de caractères interdits)
    if not re.match(r'^/[^\\:*?"<>|]*$', share_path):
        return False
    
    return True

def validate_mount_point(path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
    """
    Valide un point de montage.
    
    Args:
        path: Chemin du point de montage à valider
        
    Returns:
        Tuple[bool, Optional[str]]: (valide, message_erreur)
    """
    path = Path(path) if isinstance(path, str) else path
    
    # Vérifier que le chemin est absolu
    if not path.is_absolute():
        return False, "Le chemin du point de montage doit être absolu"
    
    # Vérifier que le répertoire parent existe
    if not path.parent.exists():
        return False, f"Le répertoire parent {path.parent} n'existe pas"
    
    # Vérifier que le chemin n'est pas déjà utilisé (si le répertoire existe déjà)
    if path.exists():
        if not path.is_dir():
            return False, f"Le chemin {path} existe mais n'est pas un répertoire"
        try:
            if any(path.iterdir()):
                return False, f"Le répertoire {path} n'est pas vide"
        except PermissionError:
            return False, f"Permission refusée pour accéder à {path}"
    
    return True, None

def validate_credentials(username: str, password: str, domain: Optional[str] = None) -> bool:
    """
    Valide des identifiants de connexion.
    
    Args:
        username: Nom d'utilisateur
        password: Mot de passe
        domain: Domaine (optionnel)
        
    Returns:
        bool: True si valide, False sinon
    """
    if not username or not password:
        return False
    
    # Vérifier la longueur minimale du nom d'utilisateur
    if len(username) < 1:
        return False
    
    # Vérifier la longueur minimale du mot de passe
    if len(password) < 1:
        return False
    
    # Vérifier le format du domaine si spécifié
    if domain and not re.match(r'^[a-zA-Z0-9.-]+$', domain):
        return False
    
    return True

def validate_fs_type(fs_type: str) -> bool:
    """
    Valide un type de système de fichiers.
    
    Args:
        fs_type: Type de système de fichiers à valider
        
    Returns:
        bool: True si valide, False sinon
    """
    return fs_type.lower() in ('cifs', 'nfs', 'nfs4')
