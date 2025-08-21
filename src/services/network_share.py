"""
Service pour gérer les opérations liées aux partages réseau.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..utils.system import (
    ensure_directory,
    is_mounted,
    mount_share as system_mount_share,
    unmount_share as system_unmount_share,
)
from ..utils.credentials import CredentialsManager
from ..utils.fstab import Fstab
from ..utils.validators import validate_hostname, validate_share_path

logger = logging.getLogger(__name__)

class NetworkShareService:
    """Service pour gérer les opérations liées aux partages réseau."""
    
    def __init__(self, fstab_path: str = "/etc/fstab", credentials_dir: str = "~/.cifs_credentials"):
        """Initialise le service de partage réseau."""
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
        """Monte un partage réseau."""
        # Validation des entrées
        if not validate_hostname(server):
            return False, f"Nom de serveur invalide: {server}"
            
        if not validate_share_path(share):
            return False, f"Chemin de partage invalide: {share}"
        
        mount_point = Path(mount_point).resolve()
        
        # Vérifier si le point de montage est déjà utilisé
        if is_mounted(mount_point):
            return False, f"Le point de montage {mount_point} est déjà utilisé"
        
        # Créer le point de montage s'il n'existe pas
        try:
            ensure_directory(mount_point)
        except OSError as e:
            return False, f"Impossible de créer le point de montage {mount_point}: {e}"
        
        # Préparer la source du partage
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
            
            # Ajouter à fstab si demandé
            if add_to_fstab:
                self._add_to_fstab(
                    source=source,
                    mount_point=mount_point,
                    fs_type=fs_type,
                    options=options or "defaults",
                    comment=f"Ajouté par NetworkMounter: {server}/{share}"
                )
            
            return True, f"Partage monté avec succès sur {mount_point}"
            
        except Exception as e:
            logger.error("Échec du montage de %s: %s", source, str(e))
            return False, f"Échec du montage: {str(e)}"
    
    def unmount_share(
        self,
        mount_point: Union[str, Path],
        force: bool = False,
        remove_from_fstab: bool = False
    ) -> Tuple[bool, str]:
        """Démonte un partage réseau."""
        mount_point = Path(mount_point).resolve()
        
        if not is_mounted(mount_point):
            return False, f"Le point de montage {mount_point} n'est pas monté"
        
        try:
            system_unmount_share(mount_point, force)
            
            if remove_from_fstab:
                self._remove_from_fstab(mount_point)
            
            return True, f"Partage démonté avec succès: {mount_point}"
            
        except Exception as e:
            logger.error("Échec du démontage de %s: %s", mount_point, str(e))
            return False, f"Échec du démontage: {str(e)}"
    
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
        """Ajoute une entrée au fichier fstab."""
        try:
            mount_point = str(Path(mount_point).resolve())
            
            if self.fstab.find_entries_by_mount_point(mount_point):
                return False, f"Une entrée existe déjà pour {mount_point}"
            
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
            return True, "Configuration ajoutée à fstab"
            
        except Exception as e:
            logger.error("Erreur lors de l'ajout à fstab: %s", e)
            return False, f"Erreur lors de l'ajout à fstab: {str(e)}"
    
    def _remove_from_fstab(self, mount_point: Union[str, Path]) -> Tuple[bool, str]:
        """Supprime une entrée de fstab."""
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
