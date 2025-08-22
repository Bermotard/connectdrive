"""
Service pour gérer les opérations liées aux partages réseau.
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
    
    def find_unused_credentials(self) -> List[Dict[str, str]]:
        """
        Trouve les fichiers d'identifiants qui ne sont plus référencés dans fstab.
        
        Returns:
            Liste des dictionnaires contenant les informations des identifiants inutilisés
        """
        logger.info("Recherche des identifiants non utilisés...")
        
        # Récupérer tous les fichiers d'identifiants
        credential_files = self.credentials_manager.list_credential_files()
        logger.info(f"Fichiers d'identifiants trouvés: {[str(f) for f in credential_files]}")
        
        # Récupérer tous les chemins de credentials utilisés dans fstab
        used_cred_paths = set()
        for entry in self.fstab.entries:
            logger.debug(f"Analyse de l'entrée fstab: {entry.filesystem} -> {entry.mount_point}")
            logger.debug(f"Options: {entry.options}")
            
            if 'credentials=' in entry.options:
                # Extraire le chemin du fichier de credentials
                for opt in entry.options.split(','):
                    opt = opt.strip()
                    if opt.startswith('credentials='):
                        try:
                            # Extraire le chemin entre les guillemets s'ils existent
                            cred_path = opt.split('=', 1)[1].strip('\'\"')
                            # Convertir en chemin absolu et normaliser
                            cred_path = Path(cred_path).expanduser().resolve()
                            used_cred_paths.add(cred_path)
                            logger.info(f"Credential utilisé trouvé dans fstab: {cred_path}")
                            logger.debug(f"Chemin normalisé: {cred_path}")
                            logger.debug(f"Chemin existe: {cred_path.exists()}")
                        except Exception as e:
                            logger.error(f"Erreur lors du traitement du chemin dans fstab: {opt} - {e}")
        
        logger.info(f"Chemins de credentials utilisés dans fstab: {[str(p) for p in used_cred_paths]}")
        logger.info(f"Nombre de chemins uniques: {len(used_cred_paths)}")
        
        # Trouver les fichiers d'identifiants non référencés
        unused_creds = []
        for cred_file in credential_files:
            try:
                cred_path = cred_file.expanduser().resolve()
                is_used = False
                logger.info(f"\nVérification du fichier: {cred_path}")
                logger.info(f"Chemin normalisé: {cred_path}")
                
                # Vérifier si ce fichier est utilisé dans fstab
                for used_path in used_cred_paths:
                    try:
                        logger.debug(f"Comparaison avec le chemin utilisé: {used_path}")
                        
                        # 1. Essayer d'abord avec samefile() pour gérer les liens symboliques
                        if cred_path.exists() and used_path.exists():
                            if cred_path.samefile(used_path):
                                is_used = True
                                logger.info(f"=> FICHIER TROUVÉ (samefile): {cred_path} == {used_path}")
                                break
                        
                        # 2. Comparer les chemins normalisés
                        if str(cred_path) == str(used_path):
                            is_used = True
                            logger.info(f"=> FICHIER TROUVÉ (chemin identique): {cred_path}")
                            break
                            
                        # 3. Comparaison des noms de fichiers (au cas où les chemins seraient différents mais le fichier le même)
                        if cred_path.name == used_path.name:
                            is_used = True
                            logger.info(f"=> FICHIER TROUVÉ (même nom de fichier): {cred_path.name}")
                            break
                            
                        # 4. Vérifier les noms de fichiers similaires (avec des points/underscores différents)
                        def normalize_name(name):
                            # Remplacer les points par des underscores pour la comparaison
                            return name.replace('.', '_')
                            
                        if normalize_name(cred_path.name) == normalize_name(used_path.name):
                            is_used = True
                            logger.info(f"=> FICHIER TROUVÉ (noms similaires): {cred_path.name} ~= {used_path.name}")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Erreur lors de la comparaison des chemins {cred_path} et {used_path}: {e}")
                
                if not is_used:
                    try:
                        logger.info(f"=> FICHIER NON TROUVÉ DANS FSTAB: {cred_path}")
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
