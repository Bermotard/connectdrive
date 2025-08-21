"""
Utilitaires pour la gestion du fichier fstab.
"""
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .exceptions import FstabError
from .system import secure_file_write

logger = logging.getLogger(__name__)

class FstabEntry:
    """Représente une entrée dans le fichier fstab."""
    
    def __init__(
        self,
        filesystem: str,
        mount_point: str,
        fs_type: str,
        options: str,
        dump: int = 0,
        pass_num: int = 0,
        comment: str = ""
    ):
        """
        Initialise une entrée fstab.
        
        Args:
            filesystem: Le système de fichiers ou la source (ex: /dev/sda1 ou //serveur/partage)
            mount_point: Le point de montage (doit être un chemin absolu)
            fs_type: Le type de système de fichiers (ext4, nfs, cifs, etc.)
            options: Options de montage séparées par des virgules
            dump: Option de sauvegarde (généralement 0 ou 1)
            pass_num: Option de vérification au démarrage (0, 1, ou 2)
            comment: Commentaire optionnel pour cette entrée
        """
        self.filesystem = filesystem.strip()
        self.mount_point = str(Path(mount_point).resolve())
        self.fs_type = fs_type.strip()
        self.options = options.strip()
        self.dump = int(dump)
        self.pass_num = int(pass_num)
        self.comment = comment.strip()
    
    def __str__(self) -> str:
        """Retourne la représentation sous forme de chaîne de l'entrée fstab."""
        line = f"{self.filesystem} {self.mount_point} {self.fs_type} {self.options} {self.dump} {self.pass_num}"
        if self.comment:
            line = f"{line}  # {self.comment}"
        return line
    
    def __eq__(self, other: object) -> bool:
        """Compare deux entrées fstab en ignorant les commentaires."""
        if not isinstance(other, FstabEntry):
            return False
        return (
            self.filesystem == other.filesystem and
            self.mount_point == other.mount_point and
            self.fs_type == other.fs_type
        )

class Fstab:
    """Classe pour manipuler le fichier /etc/fstab."""
    
    def __init__(self, fstab_path: str = "/etc/fstab"):
        """
        Initialise le gestionnaire fstab.
        
        Args:
            fstab_path: Chemin vers le fichier fstab (par défaut: /etc/fstab)
        """
        self.fstab_path = Path(fstab_path)
        self.entries: List[FstabEntry] = []
        self.load()
    
    def load(self) -> None:
        """Charge les entrées du fichier fstab."""
        self.entries = []
        
        if not self.fstab_path.exists():
            raise FstabError(f"Le fichier {self.fstab_path} n'existe pas")
        
        try:
            with open(self.fstab_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Ignorer les lignes vides et les commentaires
                    if not line or line.startswith('#'):
                        if line:
                            # Conserver les commentaires
                            self.entries.append(FstabEntry("", "", "", "", 0, 0, line.lstrip('#').strip()))
                        continue
                    
                    # Découper la ligne en champs
                    parts = re.split(r'\s+', line, maxsplit=5)
                    if len(parts) < 6:
                        logger.warning("Ligne fstab mal formatée ignorée: %s", line)
                        continue
                    
                    # Extraire les champs
                    filesystem = parts[0]
                    mount_point = parts[1]
                    fs_type = parts[2]
                    options = parts[3]
                    
                    try:
                        dump = int(parts[4])
                        pass_num = int(parts[5].split('#')[0].strip())  # Enlever les commentaires
                    except (ValueError, IndexError):
                        logger.warning("Valeurs numériques invalides dans la ligne: %s", line)
                        continue
                    
                    # Extraire le commentaire s'il y en a un
                    comment = ""
                    if '#' in line:
                        comment = line.split('#', 1)[1].strip()
                    
                    self.entries.append(FstabEntry(
                        filesystem=filesystem,
                        mount_point=mount_point,
                        fs_type=fs_type,
                        options=options,
                        dump=dump,
                        pass_num=pass_num,
                        comment=comment
                    ))
                    
        except IOError as e:
            raise FstabError(f"Impossible de lire le fichier {self.fstab_path}: {e}")
    
    def save(self, backup: bool = True) -> None:
        """
        Enregistre les modifications dans le fichier fstab.
        
        Args:
            backup: Si True, crée une sauvegarde du fichier avant modification
        """
        if backup:
            backup_path = self.fstab_path.with_suffix(f".{self.fstab_path.suffix}.bak")
            try:
                shutil.copy2(self.fstab_path, backup_path)
                logger.info("Sauvegarde créée: %s", backup_path)
            except IOError as e:
                raise FstabError(f"Impossible de créer une sauvegarde: {e}")
        
        # Générer le contenu du fichier
        content = ""
        for entry in self.entries:
            if not entry.filesystem:  # C'est un commentaire
                content += f"#{entry.comment}\n"
            else:
                content += f"{entry}\n"
        
        # Écrire le fichier de manière sécurisée
        secure_file_write(self.fstab_path, content, 0o644)
        logger.info("Fichier fstab mis à jour: %s", self.fstab_path)
    
    def add_entry(
        self,
        filesystem: str,
        mount_point: str,
        fs_type: str,
        options: str = "defaults",
        dump: int = 0,
        pass_num: int = 0,
        comment: str = "",
        check_duplicate: bool = True
    ) -> bool:
        """
        Ajoute une entrée au fichier fstab.
        
        Args:
            filesystem: Le système de fichiers ou la source
            mount_point: Le point de montage
            fs_type: Le type de système de fichiers
            options: Options de montage (par défaut: "defaults")
            dump: Option de sauvegarde (0 ou 1)
            pass_num: Option de vérification au démarrage (0, 1, ou 2)
            comment: Commentaire optionnel
            check_duplicate: Si True, vérifie les doublons avant d'ajouter
            
        Returns:
            bool: True si l'entrée a été ajoutée, False si elle existe déjà
        """
        new_entry = FstabEntry(
            filesystem=filesystem,
            mount_point=mount_point,
            fs_type=fs_type,
            options=options,
            dump=dump,
            pass_num=pass_num,
            comment=comment
        )
        
        # Vérifier les doublons
        if check_duplicate and new_entry in self.entries:
            logger.warning("Entrée fstab déjà existante: %s", new_entry)
            return False
        
        self.entries.append(new_entry)
        return True
    
    def remove_entry(self, filesystem: str, mount_point: str, fs_type: str) -> bool:
        """
        Supprime une entrée du fichier fstab.
        
        Args:
            filesystem: Le système de fichiers ou la source
            mount_point: Le point de montage
            fs_type: Le type de système de fichiers
            
        Returns:
            bool: True si l'entrée a été supprimée, False sinon
        """
        target = FstabEntry(filesystem, mount_point, fs_type, "")
        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if e != target]
        return len(self.entries) < initial_count
    
    def find_entries_by_mount_point(self, mount_point: str) -> List[FstabEntry]:
        """
        Trouve toutes les entrées pour un point de montage donné.
        
        Args:
            mount_point: Chemin du point de montage
            
        Returns:
            Liste des entrées correspondantes
        """
        mount_point = str(Path(mount_point).resolve())
        return [e for e in self.entries if e.mount_point == mount_point]
    
    def find_entries_by_filesystem(self, filesystem: str) -> List[FstabEntry]:
        """
        Trouve toutes les entrées pour un système de fichiers donné.
        
        Args:
            filesystem: Nom du système de fichiers ou source
            
        Returns:
            Liste des entrées correspondantes
        """
        return [e for e in self.entries if e.filesystem == filesystem]
    
    def get_network_shares(self) -> List[FstabEntry]:
        """
        Récupère tous les partages réseau (NFS, CIFS, etc.).
        
        Returns:
            Liste des entrées de partage réseau
        """
        network_fs_types = ('nfs', 'nfs4', 'cifs', 'smb', 'smbfs')
        return [e for e in self.entries if e.fs_type.lower() in network_fs_types]
