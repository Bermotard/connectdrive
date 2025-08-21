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
