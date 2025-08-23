"""
Utilitaires pour les opérations système sécurisées.
"""
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Union
from .exceptions import (
    NetworkMounterError,
    MountError,
    UnmountError,
    FstabError,
    CredentialsError
)

logger = logging.getLogger(__name__)

def run_command(
    command: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[dict] = None,
    check: bool = True,
    capture_output: bool = True,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """
    Exécute une commande système de manière sécurisée.
    
    Args:
        command: Commande à exécuter (peut être une chaîne ou une liste d'arguments)
        cwd: Répertoire de travail
        env: Variables d'environnement supplémentaires
        check: Si True, lève une exception en cas d'échec
        capture_output: Si True, capture la sortie de la commande
        input_text: Texte à envoyer sur l'entrée standard
        
    Returns:
        Objet CompletedProcess contenant le résultat de la commande
        
    Raises:
        subprocess.CalledProcessError: Si la commande échoue et que check=True
    """
    if isinstance(command, str):
        shell = True
    else:
        shell = False
    
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    stdin = subprocess.PIPE if input_text is not None else None
    
    logger.debug("Exécution de la commande: %s", command)
    
    try:
        result = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            env=process_env,
            check=check,
            capture_output=capture_output,
            text=True,
            input=input_text,
            stdin=stdin,
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error("Échec de la commande %s: %s", command, e.stderr)
        raise

def ensure_directory(path: Union[str, Path], mode: int = 0o755) -> Path:
    """
    Crée un répertoire s'il n'existe pas, avec les permissions spécifiées.
    
    Args:
        path: Chemin du répertoire
        mode: Permissions à appliquer (par défaut: 0o755)
        
    Returns:
        Path: Chemin du répertoire
    """
    path = Path(path).expanduser().resolve()
    path.mkdir(mode=mode, parents=True, exist_ok=True)
    return path

def is_mounted(mount_point: Union[str, Path]) -> bool:
    """
    Vérifie si un point de montage est actif.
    
    Args:
        mount_point: Chemin du point de montage
        
    Returns:
        bool: True si le point de montage est actif
    """
    mount_point = str(Path(mount_point).resolve())
    try:
        result = run_command(["findmnt", "--noheadings", "--output", "TARGET"])
        return mount_point in result.stdout
    except subprocess.CalledProcessError:
        return False

def get_mounted_shares() -> List[dict]:
    """
    Récupère la liste des partages montés.
    
    Returns:
        Liste des partages montés avec leurs informations
    """
    try:
        result = run_command(
            ["findmnt", "-t", "cifs,nfs,nfs4", "-o", 
             "TARGET,SOURCE,FSTYPE,OPTIONS", "-n", "-P"]
        )
        shares = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
                
            parts = {}
            for item in line.split():
                if '=' in item:
                    key, value = item.split('=', 1)
                    parts[key] = value.strip('"')
            
            if 'TARGET' in parts and 'SOURCE' in parts:
                shares.append({
                    'mount_point': parts['TARGET'],
                    'source': parts['SOURCE'],
                    'fs_type': parts.get('FSTYPE', ''),
                    'options': parts.get('OPTIONS', '')
                })
                
        return shares
    except subprocess.CalledProcessError as e:
        logger.error("Impossible de récupérer la liste des partages montés: %s", e.stderr)
        return []

def secure_file_write(file_path: Union[str, Path], content: str, mode: int = 0o600) -> None:
    """
    Écrit du contenu dans un fichier de manière sécurisée.
    
    Args:
        file_path: Chemin du fichier
        content: Contenu à écrire
        mode: Permissions du fichier (par défaut: 0o600)
        
    Raises:
        CredentialsError: En cas d'échec de l'écriture du fichier
    """
    file_path = Path(file_path).expanduser().resolve()
    
    # Créer le répertoire parent s'il n'existe pas
    file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    
    # Écrire dans un fichier temporaire
    temp_path = file_path.with_suffix(f".{os.getpid()}.tmp")
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Définir les permissions
        os.chmod(temp_path, mode)
        
        # Remplacer le fichier cible
        temp_path.replace(file_path)
        
    except Exception as e:
        # Nettoyer le fichier temporaire en cas d'erreur
        if temp_path.exists():
            temp_path.unlink()
        raise CredentialsError(f"Erreur lors de l'écriture du fichier {file_path}: {e}")

def mount_share(
    source: str,
    target: Union[str, Path],
    fs_type: str = "cifs",
    options: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    domain: Optional[str] = None
) -> None:
    """
    Monte un partage réseau.
    
    Args:
        source: Source du partage (ex: //serveur/partage)
        target: Point de montage local
        fs_type: Type de système de fichiers (cifs, nfs, etc.)
        options: Options de montage
        username: Nom d'utilisateur (pour CIFS)
        password: Mot de passe (pour CIFS)
        domain: Domaine (pour CIFS)
        
    Raises:
        MountError: Si le montage échoue
    """
    target = str(Path(target).resolve())
    
    # Préparer la commande de montage
    cmd = ["mount", "-t", fs_type]
    
    # Ajouter les options
    if options:
        cmd.extend(["-o", options])
    
    # Ajouter les identifiants pour CIFS
    if fs_type.lower() == "cifs":
        creds = []
        if username:
            creds.append(f"username={username}")
        if password:
            creds.append(f"password={password}")
        if domain:
            creds.append(f"domain={domain}")
        
        if creds:
            creds_str = ",".join(creds)
            if "-o" in cmd:
                # Ajouter aux options existantes
                idx = cmd.index("-o") + 1
                cmd[idx] = f"{cmd[idx]},{creds_str}"
            else:
                cmd.extend(["-o", creds_str])
    
    # Ajouter la source et la cible
    cmd.extend([source, target])
    
    try:
        run_command(cmd)
        logger.info("Partage monté avec succès: %s sur %s", source, target)
    except subprocess.CalledProcessError as e:
        error_msg = f"Échec du montage de {source} sur {target}: {e.stderr}"
        logger.error(error_msg)
        raise MountError(error_msg)

def create_mount_point(path: Union[str, Path], mode: int = 0o755) -> Path:
    """
    Crée un répertoire de montage s'il n'existe pas.
    
    Args:
        path: Chemin du point de montage
        mode: Permissions à appliquer (par défaut: 0o755)
        
    Returns:
        Path: Chemin du point de montage
    """
    path = Path(path).expanduser().resolve()
    path.mkdir(mode=mode, parents=True, exist_ok=True)
    return path

def remove_mount_point(path: Union[str, Path], force: bool = False) -> None:
    """
    Supprime un répertoire de montage s'il est vide.
    
    Args:
        path: Chemin du point de montage
        force: Si True, supprime même si le répertoire n'est pas vide
        
    Raises:
        OSError: Si le répertoire n'est pas vide et que force=False
    """
    path = Path(path).expanduser().resolve()
    if path.exists():
        if force:
            shutil.rmtree(path)
        else:
            path.rmdir()

def get_mount_info(mount_point: Union[str, Path]) -> Optional[dict]:
    """
    Get information about a mounted filesystem.
    
    Args:
        mount_point: Path to the mount point
        
    Returns:
        Dictionary with mount information or None if not mounted
    """
    mount_point = str(Path(mount_point).resolve())
    try:
        result = run_command(["findmnt", "-n", "-o", "SOURCE,TARGET,FSTYPE,OPTIONS", mount_point])
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            return {
                'source': parts[0],
                'target': parts[1],
                'fstype': parts[2],
                'options': parts[3] if len(parts) > 3 else ''
            }
    except subprocess.CalledProcessError:
        pass
    return None

def get_network_interfaces() -> List[dict]:
    """
    Get list of network interfaces and their status.
    
    Returns:
        List of dictionaries with interface information
    """
    try:
        result = run_command(["ip", "-j", "addr", "show"])
        import json
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return []

def get_ip_address(interface: str = "") -> str:
    """
    Get the IP address of a network interface.
    
    Args:
        interface: Network interface name (empty for default)
        
    Returns:
        IP address as string or empty string if not found
    """
    try:
        cmd = ["ip", "-4", "-o", "addr", "show", interface] if interface else ["hostname", "-I"]
        result = run_command(cmd)
        if interface:
            # Parse output like: 2: eth0    inet 192.168.1.2/24 ...
            parts = result.stdout.strip().split()
            if len(parts) >= 4:
                return parts[3].split('/')[0]
        else:
            # hostname -I returns space-separated list of IPs
            return result.stdout.strip().split()[0]
    except (subprocess.CalledProcessError, IndexError):
        pass
    return ""

def get_network_connections() -> List[dict]:
    """
    Get list of active network connections.
    
    Returns:
        List of dictionaries with connection information
    """
    try:
        result = run_command(["ss", "-tunp"])
        connections = []
        # Skip header line
        for line in result.stdout.split('\n')[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                proto = parts[0]
                state = parts[1]
                local = parts[4]
                peer = parts[5] if len(parts) > 5 else ""
                connections.append({
                    'protocol': proto,
                    'state': state,
                    'local': local,
                    'peer': peer
                })
        return connections
    except subprocess.CalledProcessError:
        return []

def get_disk_usage(path: Union[str, Path]) -> dict:
    """
    Get disk usage statistics for a path.
    
    Args:
        path: Path to check
        
    Returns:
        Dictionary with disk usage information
    """
    try:
        result = run_command(["df", "-h", "--output=size,used,avail,pcent", str(path)])
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 4:
                return {
                    'total': parts[0],
                    'used': parts[1],
                    'available': parts[2],
                    'use_percent': parts[3].rstrip('%')
                }
    except subprocess.CalledProcessError:
        pass
    return {}

def get_available_shares(server: str) -> List[dict]:
    """
    Get list of available shares from a server.
    
    Args:
        server: Server address
        
    Returns:
        List of dictionaries with share information
    """
    try:
        result = run_command(["smbclient", "-L", f"//{server}", "-N"])
        shares = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'Disk' in line and '\\' in line and not line.startswith('\\'):
                parts = line.split()
                if parts:
                    shares.append({
                        'name': parts[0],
                        'type': 'Disk',
                        'description': ' '.join(parts[1:]) if len(parts) > 1 else ''
                    })
        return shares
    except subprocess.CalledProcessError:
        return []

def get_share_permissions(share_path: str) -> dict:
    """
    Get permissions for a network share.
    
    Args:
        share_path: Path to the share (e.g., //server/share)
        
    Returns:
        Dictionary with permission information
    """
    try:
        result = run_command(["smbcacls", share_path, "-N"])
        return {
            'path': share_path,
            'permissions': result.stdout.strip()
        }
    except subprocess.CalledProcessError:
        return {'path': share_path, 'permissions': 'unknown'}

def set_share_permissions(share_path: str, permissions: str) -> bool:
    """
    Set permissions for a network share.
    
    Args:
        share_path: Path to the share
        permissions: Permissions string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        run_command(["smbcacls", share_path, "-N", "-a", permissions])
        return True
    except subprocess.CalledProcessError:
        return False

def get_share_owner(share_path: str) -> dict:
    """
    Get owner information for a network share.
    
    Args:
        share_path: Path to the share
        
    Returns:
        Dictionary with owner information
    """
    try:
        result = run_command(["smbcacls", share_path, "-N"])
        # Parse owner from ACL output
        owner = "unknown"
        for line in result.stdout.split('\n'):
            if 'OWNER:' in line:
                owner = line.split('OWNER:')[1].strip()
                break
        return {
            'path': share_path,
            'owner': owner
        }
    except subprocess.CalledProcessError:
        return {'path': share_path, 'owner': 'unknown'}

def set_share_owner(share_path: str, owner: str) -> bool:
    """
    Set owner for a network share.
    
    Args:
        share_path: Path to the share
        owner: New owner
        
    Returns:
        True if successful, False otherwise
    """
    try:
        run_command(["smbcacls", share_path, "-N", "-O", owner])
        return True
    except subprocess.CalledProcessError:
        return False

def get_share_percent_used(share_path: str) -> float:
    """
    Get the percentage of used space for a network share.
    
    Args:
        share_path: Path to the share (e.g., //server/share)
        
    Returns:
        Float representing the percentage of used space (0-100)
    """
    try:
        size_info = get_share_size(share_path)
        if 'use_percent' in size_info and size_info['use_percent'] != 'unknown':
            return float(size_info['use_percent'].rstrip('%'))
    except (ValueError, KeyError):
        pass
    return 0.0

def get_share_available_space(share_path: str) -> dict:
    """
    Get available space information for a network share.
    
    Args:
        share_path: Path to the share (e.g., //server/share)
        
    Returns:
        Dictionary with available space information
    """
    # For now, we'll just call get_share_size and return its result
    # since it already provides available space information
    return get_share_size(share_path)

def get_share_used_space(share_path: str) -> dict:
    """
    Get used space information for a network share.
    
    Args:
        share_path: Path to the share (e.g., //server/share)
        
    Returns:
        Dictionary with used space information
    """
    # For now, we'll just call get_share_size and return its result
    # since it already provides used space information
    return get_share_size(share_path)

def get_share_size(share_path: str) -> dict:
    """
    Get size information for a network share.
    
    Args:
        share_path: Path to the share (e.g., //server/share)
        
    Returns:
        Dictionary with size information (total, used, free, etc.)
    """
    try:
        # First check if the share is mounted and get its mount point
        mount_info = get_mount_info(share_path)
        if mount_info and 'target' in mount_info:
            # If it's mounted, use df to get size info
            return get_disk_usage(mount_info['target'])
            
        # If not mounted, try to get size info directly (may require authentication)
        result = run_command(["smbclient", share_path, "-N", "-c", "du"])
        if result.returncode == 0:
            # Parse smbclient du output which is in blocks (usually 1024 bytes per block)
            lines = result.stdout.strip().split('\n')
            if lines and 'blocks of size' in lines[-1]:
                parts = lines[-1].split()
                if len(parts) >= 7:
                    blocks = int(parts[0].replace(',', ''))
                    block_size = int(parts[3])
                    total_bytes = blocks * block_size
                    return {
                        'total': f"{total_bytes / (1024*1024):.1f}M",
                        'used': '0',
                        'available': f"{total_bytes / (1024*1024):.1f}M",
                        'use_percent': '0'
                    }
    except (subprocess.CalledProcessError, ValueError, IndexError) as e:
        logger.warning(f"Could not get share size for {share_path}: {e}")
    
    return {'total': 'unknown', 'used': 'unknown', 'available': 'unknown', 'use_percent': '0'}

def unmount_share(mount_point: Union[str, Path], force: bool = False) -> None:
    """
    Démonte un partage réseau.
    
    Args:
        mount_point: Chemin du point de montage
        force: Si True, force le démontage même en cas d'utilisation
        
    Raises:
        UnmountError: Si le démontage échoue
    """
    mount_point = str(Path(mount_point).resolve())
    
    # Vérifier si le point de montage est bien monté
    if not is_mounted(mount_point):
        logger.warning("Le point de montage %s n'est pas monté", mount_point)
        return
    
    # Préparer la commande de démontage
    cmd = ["umount"]
    if force:
        cmd.append("-f")
    cmd.append(mount_point)
    
    try:
        run_command(cmd)
        logger.info("Partage démonté avec succès: %s", mount_point)
    except subprocess.CalledProcessError as e:
        error_msg = f"Échec du démontage de {mount_point}: {e.stderr}"
        logger.error(error_msg)
        raise UnmountError(error_msg)
