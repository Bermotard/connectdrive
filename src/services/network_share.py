"""
Service for managing network share operations.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Set up file logging
log_file = os.path.expanduser('~/network_mounter_debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler()
    ]
)

from src.utils.system import (
    run_command,
    is_mounted,
    create_mount_point,
    remove_mount_point,
    get_mount_info,
    get_network_interfaces,
    get_ip_address,
    get_network_connections,
    get_disk_usage,
    get_mounted_shares,
    get_available_shares,
    get_share_permissions,
    set_share_permissions,
    get_share_owner,
    set_share_owner,
    get_share_size,
    get_share_used_space,
    get_share_available_space,
    get_share_percent_used
)

from src.utils.fstab import Fstab
from src.utils.credentials import CredentialsManager
from src.utils.validators import validate_hostname, validate_share_path

logger = logging.getLogger(__name__)

class NetworkShareService:
    """Service for managing network share operations."""
    
    def __init__(self, fstab_path: str = "/etc/fstab", credentials_dir: str = "~/.cifs_credentials"):
        """Initialize the network share service."""
        self.fstab = Fstab(fstab_path)
        self.credentials_manager = CredentialsManager(credentials_dir)
    
    def mount_share(
        self,
        server: str,
        share: str,
        mount_point: Union[str, Path],
        fs_type: str = "cifs",
        options: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
        save_credentials: bool = False,
        add_to_fstab: bool = False
    ) -> Tuple[bool, str]:
        """Mount a network share."""
        # Input validation
        if not validate_hostname(server):
            return False, f"Invalid server name: {server}"
            
        if not validate_share_path(share):
            return False, f"Invalid share path: {share}"
        
        mount_point = Path(mount_point).resolve()
        
        # Check if mount point is already in use
        if is_mounted(mount_point):
            return False, f"Mount point {mount_point} is already in use"
        
        # Create mount point if it doesn't exist
        try:
            ensure_directory(mount_point)
        except OSError as e:
            return False, f"Failed to create mount point {mount_point}: {e}"
        
        # Prepare the share source
        source = f"//{server}/{share.lstrip('/')}" if fs_type.lower() in ('cifs', 'smb') else f"{server}:{share}"
        
        # Monter le partage
        try:
            system_mount_share(
                source=source,
                target=mount_point,
                fs_type=fs_type,
                options=options,
                username=username,
                password=password,
                domain=domain
            )
            
            # Add to fstab if requested
            if add_to_fstab:
                self._add_to_fstab(
                    source=source,
                    mount_point=mount_point,
                    fs_type=fs_type,
                    options=options or "defaults",
                    comment=f"Added by NetworkMounter: {server}/{share}"
                )
            
            return True, f"Share successfully mounted on {mount_point}"
            
        except Exception as e:
            logger.error("Failed to mount %s: %s", source, str(e))
            return False, f"Mount failed: {str(e)}"
    
    def unmount_share(
        self,
        mount_point: Union[str, Path],
        force: bool = False,
        remove_from_fstab: bool = False
    ) -> Tuple[bool, str]:
        """Unmount a network share."""
        mount_point = Path(mount_point).resolve()
        
        if not is_mounted(mount_point):
            return False, f"Mount point {mount_point} is not mounted"
        
        try:
            system_unmount_share(mount_point, force)
            
            if remove_from_fstab:
                self._remove_from_fstab(mount_point)
            
            return True, f"Share successfully unmounted: {mount_point}"
            
        except Exception as e:
            logger.error("Failed to unmount %s: %s", mount_point, str(e))
            return False, f"Unmount failed: {str(e)}"
    
    def _add_to_fstab(
        self,
        source: str,
        mount_point: Union[str, Path],
        fs_type: str,
        options: str = "defaults",
        dump: int = 0,
        pass_num: int = 0,
        comment: str = ""
    ) -> Tuple[bool, str]:
        """Add an entry to the fstab file."""
        try:
            mount_point = str(Path(mount_point).resolve())
            
            if self.fstab.find_entries_by_mount_point(mount_point):
                return False, f"An entry already exists for {mount_point}"
            
            self.fstab.add_entry(
                filesystem=source,
                mount_point=mount_point,
                fs_type=fs_type,
                options=options,
                dump=dump,
                pass_num=pass_num,
                comment=comment
            )
            
            self.fstab.save()
            return True, "Configuration added to fstab"
            
        except Exception as e:
            logger.error("Error while adding to fstab: %s", e)
            return False, f"Error while adding to fstab: {str(e)}"
    
    def find_unused_credentials(self) -> List[Dict[str, str]]:
        """
        Find credential files that are no longer referenced in fstab.
        
        Returns:
            List of dictionaries containing information about unused credentials
        """
        logger.info("Searching for unused credentials...")
        
        # Get all credential files
        credential_files = self.credentials_manager.list_credential_files()
        logger.info(f"Found credential files: {[str(f) for f in credential_files]}")
        
        # Get all credential paths used in fstab
        used_cred_paths = set()
        for entry in self.fstab.entries:
            logger.debug(f"Analyse de l'entrée fstab: {entry.filesystem} -> {entry.mount_point}")
            logger.debug(f"Options: {entry.options}")
            
            if 'credentials=' in entry.options:
                # Extract the credential file path
                for opt in entry.options.split(','):
                    opt = opt.strip()
                    if opt.startswith('credentials='):
                        try:
                            # Extraire le chemin entre les guillemets s'ils existent
                            cred_path = opt.split('=', 1)[1].strip('\'\"')
                            # Convertir en chemin absolu et normaliser
                            cred_path = Path(cred_path).expanduser().resolve()
                            used_cred_paths.add(cred_path)
                            logger.info(f"Credential found in fstab: {cred_path}")
                            logger.debug(f"Normalized path: {cred_path}")
                            logger.debug(f"Path exists: {cred_path.exists()}")
                        except Exception as e:
                            logger.error(f"Error processing path in fstab: {opt} - {e}")
        
        logger.info(f"Credential paths used in fstab: {[str(p) for p in used_cred_paths]}")
        logger.info(f"Number of unique paths: {len(used_cred_paths)}")
        
        # Find unreferenced credential files
        unused_creds = []
        for cred_file in credential_files:
            try:
                cred_path = cred_file.expanduser().resolve()
                is_used = False
                logger.info(f"\nChecking file: {cred_path}")
                logger.info(f"Normalized path: {cred_path}")
                
                # Check if this file is used in fstab
                for used_path in used_cred_paths:
                    try:
                        logger.debug(f"Comparing with used path: {used_path}")
                        
                        # 1. First try with samefile() to handle symlinks
                        if cred_path.exists() and used_path.exists():
                            if cred_path.samefile(used_path):
                                is_used = True
                                logger.info(f"=> FILE FOUND (samefile): {cred_path} == {used_path}")
                                break
                        
                        # 2. Compare normalized paths
                        if str(cred_path) == str(used_path):
                            is_used = True
                            logger.info(f"=> FILE FOUND (identical path): {cred_path}")
                            break
                            
                        # 3. Compare filenames (in case paths are different but files are the same)
                        if cred_path.name == used_path.name:
                            is_used = True
                            logger.info(f"=> FILE FOUND (same filename): {cred_path.name}")
                            break
                            
                        # 4. Check for similar filenames (with different dots/underscores)
                        def normalize_name(name):
                            # Replace dots with underscores for comparison
                            return name.replace('.', '_')
                            
                        if normalize_name(cred_path.name) == normalize_name(used_path.name):
                            is_used = True
                            logger.info(f"=> FILE FOUND (similar names): {cred_path.name} ~= {used_path.name}")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error comparing paths {cred_path} and {used_path}: {e}")
                
                if not is_used:
                    try:
                        logger.info(f"=> FILE NOT FOUND IN FSTAB: {cred_path}")
                        creds = self.credentials_manager.parse_credentials_file(cred_path)
                        unused_creds.append({
                            'path': str(cred_path),
                            'username': creds.get('username', ''),
                            'domain': creds.get('domain', ''),
                            'file': cred_path.name,
                            'size': cred_path.stat().st_size,
                            'mtime': cred_path.stat().st_mtime
                        })
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture du fichier {cred_path}: {e}")
                else:
                    logger.info(f"=> FICHIER DÉJÀ UTILISÉ DANS FSTAB: {cred_path}")
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement du fichier {cred_file}: {e}")
        
        logger.info(f"\nRésumé: {len(unused_creds)} fichiers d'identifiants inutilisés trouvés sur {len(credential_files)} fichiers analysés")
        return unused_creds
        
    def _remove_from_fstab(self, mount_point: Union[str, Path]) -> Tuple[bool, str]:
        """Remove an entry from fstab."""
        try:
            mount_point = str(Path(mount_point).resolve())
            entries = self.fstab.find_entries_by_mount_point(mount_point)
            
            if not entries:
                return False, f"Aucune entrée trouvée pour {mount_point}"
            
            for entry in entries:
                self.fstab.remove_entry(entry.filesystem, entry.mount_point, entry.fs_type)
            
            self.fstab.save()
            return True, "Entrée supprimée de fstab"
            
        except Exception as e:
            logger.error("Erreur lors de la suppression de fstab: %s", e)
            return False, f"Erreur lors de la suppression de fstab: {str(e)}"
