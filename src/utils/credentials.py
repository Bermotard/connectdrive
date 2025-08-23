"""
Gestion sécurisée des identifiants pour les partages réseau.
"""
import os
import logging
import uuid
import stat
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .exceptions import CredentialsError
from .system import secure_file_write

logger = logging.getLogger(__name__)

class CredentialsManager:
    """Gère le stockage sécurisé des identifiants pour les partages réseau."""
    
    def __init__(self, credentials_dir: str = "~/.cifs_credentials"):
        """
        Initialise le gestionnaire d'identifiants.
        
        Args:
            credentials_dir: Directory to store credentials files
        """
        self.credentials_dir = Path(credentials_dir).expanduser().resolve()
        self.ensure_credentials_dir()
    
    def ensure_credentials_dir(self) -> None:
        """Create the credentials directory if it doesn't exist."""
        try:
            self.credentials_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            logger.debug("Credentials directory: %s", self.credentials_dir)
        except OSError as e:
            raise CredentialsError(
                f"Failed to create credentials directory {self.credentials_dir}: {e}"
            )
    
    def create_credentials_file(
        self,
        username: str,
        password: str,
        domain: Optional[str] = None,
        share_name: Optional[str] = None,
        server: Optional[str] = None
    ) -> str:
        """
        Creates a secure credentials file.
        
        Args:
            username: Username
            password: Password
            domain: Domain (optional)
            share_name: Share name (for the filename)
            server: Server name (for the filename)
            
        Returns:
            Path to the created credentials file
            
        Raises:
            CredentialsError: If there's an error creating the file
        """
        # Generate a unique filename
        if share_name and server:
            # Use a filename based on the server and share
            safe_server = "".join(c if c.isalnum() else "_" for c in server)
            safe_share = "".join(c if c.isalnum() else "_" for c in share_name)
            filename = f"{safe_server}_{safe_share}_{uuid.uuid4().hex[:8]}.cred"
        else:
            # Use a random filename
            filename = f"credentials_{uuid.uuid4().hex}.cred"
        
        creds_path = self.credentials_dir / filename
        
        # Build the file content
        content = [
            f"username={username}",
            f"password={password}"
        ]
        
        if domain:
            content.append(f"domain={domain}")
        
        # Write the file securely
        try:
            secure_file_write(creds_path, "\n".join(content), 0o600)
            logger.info("Credentials file created: %s", creds_path)
            return str(creds_path)
            
        except Exception as e:
            raise CredentialsError(
                f"Error creating credentials file: {e}"
            )
    
    def parse_credentials_file(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """
        Read and parse a credentials file.
        
        Args:
            file_path: Path to the credentials file
            
        Returns:
            Dictionary containing the credentials
            
        Raises:
            CredentialsError: If the file is inaccessible or malformed
        """
        file_path = Path(file_path).expanduser().resolve()
        
        if not file_path.exists():
            raise CredentialsError(f"Credentials file {file_path} does not exist")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            creds = {}
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                creds[key.strip().lower()] = value.strip()
            
            # Check for required fields
            if 'username' not in creds or 'password' not in creds:
                raise CredentialsError("Incomplete credentials file")
            
            return creds
            
        except (IOError, ValueError) as e:
            raise CredentialsError(
                f"Error reading file {file_path}: {e}"
            )
    
    def delete_credentials_file(self, file_path: Union[str, Path]) -> bool:
        """
        Delete a credentials file securely.
        
        Args:
            file_path: Path to the credentials file
            file_path: Chemin vers le fichier d'identifiants
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        file_path = Path(file_path).expanduser().resolve()
        
        # Vérifier que le fichier est bien dans le répertoire des identifiants
        if not file_path.is_relative_to(self.credentials_dir):
            logger.warning("Tentative de suppression d'un fichier en dehors du répertoire des identifiants: %s", file_path)
            return False
        
        try:
            if file_path.exists():
                # Écraser le contenu avant suppression
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(1024))
                file_path.unlink()
                logger.info("Fichier d'identifiants supprimé: %s", file_path)
            return True
            
        except OSError as e:
            logger.error("Error deleting file %s: %s", file_path, e)
            return False
    
    def list_credential_files(self) -> List[Path]:
        """
        Liste tous les fichiers d'identifiants dans le répertoire des identifiants.
        
        Returns:
            Liste des chemins vers les fichiers d'identifiants
        """
        return list(self.credentials_dir.glob("*.cred"))
        
    def cleanup_old_credentials(self, max_age_days: int = 30) -> Tuple[int, int]:
        """
        Nettoie les fichiers d'identifiants anciens.
        
        Args:
            max_age_days: Maximum age in days before deletion
            
        Returns:
            Tuple (nombre de fichiers supprimés, nombre d'erreurs)
        """
        import time
        from datetime import datetime, timedelta
        
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted = 0
        errors = 0
        
        try:
            for cred_file in self.credentials_dir.glob("*.cred"):
                try:
                    file_stat = cred_file.stat()
                    if file_stat.st_mtime < cutoff_time:
                        if self.delete_credentials_file(cred_file):
                            deleted += 1
                        else:
                            errors += 1
                except OSError as e:
                    logger.error("Error processing %s: %s", cred_file, e)
                    errors += 1
            
            logger.info("Credentials cleanup: %d files deleted, %d errors", deleted, errors)
            return deleted, errors
            
        except Exception as e:
            logger.error("Error during credentials cleanup: %s", e)
            return deleted, errors + 1
