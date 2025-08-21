"""
Service pour gérer les opérations de montage et de démontage des partages réseau.
"""
import subprocess
import shlex
import os
from typing import Dict, Optional, Tuple

from config import settings

class MountService:
    """Service pour gérer les opérations de montage."""
    
    def mount_share(
        self,
        server: str,
        share: str,
        mount_point: str,
        username: str = "",
        password: str = "",
        domain: str = "",
        filesystem: str = "cifs",
        options: str = ""
    ) -> Tuple[bool, str]:
        """
        Monte un partage réseau.
        
        Args:
            server: Adresse du serveur
            share: Nom du partage
            mount_point: Point de montage local
            username: Nom d'utilisateur (optionnel)
            password: Mot de passe (optionnel)
            domain: Domaine (optionnel)
            filesystem: Type de système de fichiers (par défaut: cifs)
            options: Options de montage supplémentaires
            
        Returns:
            Tuple (succès, message)
        """
        try:
            # Créer le point de montage s'il n'existe pas
            os.makedirs(mount_point, exist_ok=True)
            
            # Construire la commande de montage
            cmd = ["sudo", "mount", "-t", filesystem]
            
            # Ajouter les options
            if options:
                cmd.extend(["-o", options])
                
            # Ajouter les informations d'authentification si fournies
            if username:
                creds = f"username={username}"
                if password:
                    creds += f",password={shlex.quote(password)}"
                if domain:
                    creds += f",domain={domain}"  
                cmd.extend(["-o", creds])
            
            # Ajouter la source et la destination
            source = f"//{server}/{share}" if filesystem == "cifs" else f"{server}:{share}"
            cmd.extend([source, mount_point])
            
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return True, f"Partage monté avec succès sur {mount_point}"
            
        except subprocess.CalledProcessError as e:
            return False, f"Échec du montage: {e.stderr}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"
    
    def unmount_share(self, mount_point: str) -> Tuple[bool, str]:
        """
        Démonte un partage réseau.
        
        Args:
            mount_point: Point de montage à démonter
            
        Returns:
            Tuple (succès, message)
        """
        try:
            if not os.path.ismount(mount_point):
                return False, f"{mount_point} n'est pas un point de montage valide"
                
            result = subprocess.run(
                ["sudo", "umount", mount_point],
                capture_output=True,
                text=True,
                check=True
            )
            
            return True, f"Point de montage {mount_point} démonté avec succès"
            
        except subprocess.CalledProcessError as e:
            return False, f"Échec du démontage: {e.stderr}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"
    
    def list_mounts(self) -> Tuple[bool, str]:
        """
        Liste les points de montage actifs.
        
        Returns:
            Tuple (succès, résultat ou message d'erreur)
        """
        try:
            result = subprocess.run(
                ["mount"],
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
            
        except subprocess.CalledProcessError as e:
            return False, f"Impossible de lister les points de montage: {e.stderr}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"
