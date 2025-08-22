"""
Service pour gérer les opérations liées au fichier fstab.
"""
import subprocess
import shlex
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import tkinter as tk
from ..config import settings
from .mount_service import MountService

class FstabService:
    """Service pour gérer les opérations liées à fstab."""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        """Initialize the FstabService.
        
        Args:
            parent_window: Parent window for dialogs
        """
        self._fstab_path = Path(settings.FSTAB_PATH)
        self._mount_service = MountService()  # For sudo commands
        self.parent_window = parent_window
        
    @property
    def fstab_path(self) -> Path:
        """Retourne le chemin vers le fichier fstab."""
        return self._fstab_path
        
    @fstab_path.setter
    def fstab_path(self, path):
        """Définit le chemin vers le fichier fstab."""
        self._fstab_path = Path(path).resolve()
    
    def read_fstab(self) -> Tuple[bool, str]:
        """Lit le contenu du fichier fstab."""
        try:
            with open(self.fstab_path, 'r') as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"Impossible de lire {self.fstab_path}: {str(e)}"
    
    def add_fstab_entry(
        self,
        server: str,
        share: str,
        mount_point: str,
        filesystem: str = "cifs",
        options: str = "",
        username: str = "",
        password: str = "",
        domain: str = "",
        dump: int = 0,
        pass_num: int = 0
    ) -> Tuple[bool, str]:
        """
        Ajoute une entrée au fichier fstab.
        
        Returns:
            Tuple (succès, message)
        """
        try:
            # Vérifier si le point de montage existe
            mount_point = Path(mount_point).resolve()
            if not mount_point.exists():
                os.makedirs(mount_point, exist_ok=True)
            
            # Construire la source
            source = f"//{server}/{share}" if filesystem == "cifs" else f"{server}:{share}"
            
            # Gérer les informations d'authentification
            if username or password or domain:
                creds_file = self._create_credentials_file(
                    username=username,
                    password=password,
                    domain=domain,
                    server=server,
                    share=share
                )
                options = f"{options},credentials={creds_file}" if options else f"credentials={creds_file}"
            
            # Construire la ligne fstab
            fstab_line = f"{source} {mount_point} {filesystem} {options} {dump} {pass_num}\n"
            
            # Lire le contenu actuel de fstab
            success, content = self.read_fstab()
            if not success:
                return False, content
            
            # Vérifier si l'entrée existe déjà
            if source in content and str(mount_point) in content:
                return False, "Cette entrée existe déjà dans fstab"
            
            # Prepare the entry to add
            entry_to_add = f"\n# Added by NetworkMounter\n{fstab_line}"
            
            # Create a temporary file with the new content
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
                tmp_file.write(content + entry_to_add)
                tmp_path = tmp_file.name
            
            try:
                # Use sudo to copy the temporary file to the actual fstab
                success, message = self._mount_service._run_sudo_command(
                    ["cp", tmp_path, str(self.fstab_path)],
                    parent_window=self.parent_window
                )
                
                if not success:
                    return False, f"Failed to update fstab: {message}"
                
                # Set correct permissions
                self._mount_service._run_sudo_command(
                    ["chmod", "644", str(self.fstab_path)],
                    parent_window=self.parent_window
                )
                
                return True, "Entry successfully added to fstab"
                
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {tmp_path}: {e}")
            
        except Exception as e:
            return False, f"Erreur lors de l'ajout à fstab: {str(e)}"
    
    def _create_credentials_file(
        self,
        username: str,
        password: str,
        domain: str,
        server: str,
        share: str
    ) -> str:
        """
        Crée un fichier d'identifiants sécurisé.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            domain: Domaine
            server: Serveur (pour le nom du fichier)
            share: Partage (pour le nom du fichier)
            
        Returns:
            Chemin vers le fichier d'identifiants
        """
        # Créer le répertoire des identifiants s'il n'existe pas
        creds_dir = Path(settings.CREDENTIALS_DIR).expanduser()
        creds_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        
        # Créer un nom de fichier unique
        safe_server = "".join(c if c.isalnum() else "_" for c in f"{server}_{share}")
        creds_file = creds_dir / f"{safe_server}.cred"
        
        # Écrire les identifiants dans le fichier
        with open(creds_file, 'w') as f:
            f.write(f"username={username}\n")
            f.write(f"password={password}\n")
            if domain:
                f.write(f"domain={domain}\n")
        
        # Définir les permissions sécurisées
        os.chmod(creds_file, 0o600)
        
        return str(creds_file)
