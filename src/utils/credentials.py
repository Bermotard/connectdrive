"""
Gestion sécurisée des identifiants pour les partages réseau.
"""
import os
import logging
import uuid
import stat
from pathlib import Path
from typing import Dict, Optional, Tuple

from .exceptions import CredentialsError
from .system import secure_file_write

logger = logging.getLogger(__name__)

class CredentialsManager:
    """Gère le stockage sécurisé des identifiants pour les partages réseau."""
    
    def __init__(self, credentials_dir: str = "~/.cifs_credentials"):
        """
        Initialise le gestionnaire d'identifiants.
        
        Args:
            credentials_dir: Répertoire de stockage des fichiers d'identifiants
        """
        self.credentials_dir = Path(credentials_dir).expanduser().resolve()
        self.ensure_credentials_dir()
    
    def ensure_credentials_dir(self) -> None:
        """Crée le répertoire des identifiants s'il n'existe pas."""
        try:
            self.credentials_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            logger.debug("Répertoire des identifiants: %s", self.credentials_dir)
        except OSError as e:
            raise CredentialsError(
                f"Impossible de créer le répertoire des identifiants {self.credentials_dir}: {e}"
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
        Crée un fichier d'identifiants sécurisé.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            domain: Domaine (optionnel)
            share_name: Nom du partage (pour le nom du fichier)
            server: Nom du serveur (pour le nom du fichier)
            
        Returns:
            Chemin vers le fichier d'identifiants créé
            
        Raises:
            CredentialsError: En cas d'erreur lors de la création du fichier
        """
        # Générer un nom de fichier unique
        if share_name and server:
            # Utiliser un nom basé sur le serveur et le partage
            safe_server = "".join(c if c.isalnum() else "_" for c in server)
            safe_share = "".join(c if c.isalnum() else "_" for c in share_name)
            filename = f"{safe_server}_{safe_share}_{uuid.uuid4().hex[:8]}.cred"
        else:
            # Utiliser un nom aléatoire
            filename = f"credentials_{uuid.uuid4().hex}.cred"
        
        creds_path = self.credentials_dir / filename
        
        # Construire le contenu du fichier
        content = [
            f"username={username}",
            f"password={password}"
        ]
        
        if domain:
            content.append(f"domain={domain}")
        
        # Écrire le fichier de manière sécurisée
        try:
            secure_file_write(creds_path, "\n".join(content), 0o600)
            logger.info("Fichier d'identifiants créé: %s", creds_path)
            return str(creds_path)
            
        except Exception as e:
            raise CredentialsError(
                f"Erreur lors de la création du fichier d'identifiants: {e}"
            )
    
    def parse_credentials_file(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """
        Lit et analyse un fichier d'identifiants.
        
        Args:
            file_path: Chemin vers le fichier d'identifiants
            
        Returns:
            Dictionnaire contenant les identifiants
            
        Raises:
            CredentialsError: Si le fichier est inaccessible ou mal formaté
        """
        file_path = Path(file_path).expanduser().resolve()
        
        if not file_path.exists():
            raise CredentialsError(f"Le fichier d'identifiants {file_path} n'existe pas")
        
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
            
            # Vérifier les champs obligatoires
            if 'username' not in creds or 'password' not in creds:
                raise CredentialsError("Fichier d'identifiants incomplet")
            
            return creds
            
        except (IOError, ValueError) as e:
            raise CredentialsError(f"Erreur lors de la lecture du fichier {file_path}: {e}")
    
    def delete_credentials_file(self, file_path: Union[str, Path]) -> bool:
        """
        Supprime un fichier d'identifiants de manière sécurisée.
        
        Args:
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
            logger.error("Erreur lors de la suppression du fichier %s: %s", file_path, e)
            return False
    
    def cleanup_old_credentials(self, max_age_days: int = 30) -> Tuple[int, int]:
        """
        Nettoie les fichiers d'identifiants anciens.
        
        Args:
            max_age_days: Âge maximum en jours avant suppression
            
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
                    logger.error("Erreur lors du traitement de %s: %s", cred_file, e)
                    errors += 1
            
            logger.info("Nettoyage des identifiants: %d fichiers supprimés, %d erreurs", deleted, errors)
            return deleted, errors
            
        except Exception as e:
            logger.error("Erreur lors du nettoyage des identifiants: %s", e)
            return deleted, errors + 1
