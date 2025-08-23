"""
Validators for NetworkMounter application user inputs.
"""
import re
import ipaddress
from typing import Optional, Tuple, Union
from pathlib import Path
from .exceptions import ValidationError

def validate_hostname(hostname: str) -> bool:
    """
    Validates a hostname or IP address.
    
    Args:
        hostname: Hostname or IP address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not hostname:
        return False
    
    # Check if it's a valid IP address
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    
    # Check if it's a valid hostname
    if len(hostname) > 255:
        return False
    
    # A hostname cannot start or end with a dot
    if hostname[-1] == "." or hostname[0] == ".":
        return False
    
    # Check each part of the hostname
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def validate_share_path(share_path: str) -> bool:
    """
    Validates a network share path.
    
    Args:
        share_path: Share path to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not share_path:
        return False
    
    # Check basic format (must start with / and not contain forbidden characters)
    if not re.match(r'^/[^\\:*?"<>|]*$', share_path):
        return False
    
    return True

def validate_mount_point(path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
    """
    Validates a mount point.
    
    Args:
        path: Mount point path to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    path = Path(path) if isinstance(path, str) else path
    
    # Check that the path is absolute
    if not path.is_absolute():
        return False, "Mount point path must be absolute"
    
    # Check that the parent directory exists
    if not path.parent.exists():
        return False, f"Parent directory {path.parent} does not exist"
    
    # Check that the path is not already in use (if directory exists)
    if path.exists():
        if not path.is_dir():
            return False, f"Path {path} exists but is not a directory"
        try:
            if any(path.iterdir()):
                return False, f"Directory {path} is not empty"
        except PermissionError:
            return False, f"Permission denied when accessing {path}"
    
    return True, None

def validate_credentials(username: str, password: str, domain: Optional[str] = None) -> bool:
    """
    Validates login credentials.
    
    Args:
        username: Username
        password: Password
        domain: Domain (optional)
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not username or not password:
        return False
    
    # Check minimum username length
    if len(username) < 1:
        return False
    
    # Check minimum password length
    if len(password) < 1:
        return False
    
    # Check the domain format if specified
    if domain and not re.match(r'^[a-zA-Z0-9.-]+$', domain):
        return False
    
    return True

def validate_fs_type(fs_type: str) -> bool:
    """
    Validates a filesystem type.
    
    Args:
        fs_type: Filesystem type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return fs_type.lower() in ('cifs', 'nfs', 'nfs4')
