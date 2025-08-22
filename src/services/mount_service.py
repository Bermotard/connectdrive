"""
Service pour gérer les opérations de montage et de démontage des partages réseau.
"""
import subprocess
import shlex
import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Union

from ..config import settings
from ..utils.credentials import CredentialsManager
from ..utils.exceptions import CredentialsError, MountError
from ..gui.dialogs.sudo_password_dialog import SudoPasswordDialog
import tkinter as tk

logger = logging.getLogger(__name__)

class MountService:
    """Service pour gérer les opérations de montage."""
    
    def __init__(self):
        """Initialise le service de montage avec le gestionnaire d'identifiants."""
        from .network_share import NetworkShareService
        self.credentials_manager = CredentialsManager()
        self.active_credentials = {}  # Pour garder une trace des fichiers de credentials actifs
        self.network_share_service = NetworkShareService()

    def _run_sudo_command(self, command: List[str], parent_window: Optional[tk.Tk] = None) -> Tuple[bool, str]:
        """
        Exécute une commande avec sudo en demandant le mot de passe si nécessaire.
        
        Args:
            command: Commande à exécuter
            parent_window: Fenêtre parente pour la boîte de dialogue
            
        Returns:
            Tuple (succès, sortie ou message d'erreur)
        """
        # Demander le mot de passe sudo
        if parent_window is None:
            parent_window = tk.Tk()
            parent_window.withdraw()  # Cacher la fenêtre racine
        
        password = SudoPasswordDialog.ask_sudo_password(parent_window)
        if password is None:
            return False, "Authentification annulée par l'utilisateur"
        
        # Créer un fichier temporaire pour le mot de passe
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write(f"{password}\n")
            temp_file = f.name
        
        try:
            # Définir les permissions du fichier
            os.chmod(temp_file, 0o600)
            
            # Construire la commande avec sudo -S pour lire le mot de passe depuis stdin
            sudo_cmd = ["sudo", "-S"] + command
            
            # Exécuter la commande
            result = subprocess.run(
                sudo_cmd,
                input=password + "\n",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                error_msg = result.stderr or f"Échec de la commande (code {result.returncode})"
                logger.error("Erreur d'exécution: %s", error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Délai dépassé lors de l'exécution de la commande"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
            
        finally:
            # Nettoyer le fichier temporaire
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning("Impossible de supprimer le fichier temporaire: %s", str(e))
    
    def mount_share(
        self,
        server: str,
        share: str,
        mount_point: str,
        username: str = "",
        password: str = "",
        domain: str = "",
        filesystem: str = "cifs",
        options: str = "",
        parent_window: Optional[tk.Tk] = None
    ) -> Tuple[bool, str]:
        """
        Monte un partage réseau en utilisant un fichier d'identifiants pour la sécurité.
        
        Args:
            server: Adresse du serveur
            share: Nom du partage
            mount_point: Point de montage local
            username: Nom d'utilisateur (optionnel)
            password: Mot de passe (optionnel, peut contenir des caractères spéciaux)
            domain: Domaine (optionnel)
            filesystem: Type de système de fichiers (par défaut: cifs)
            options: Options de montage supplémentaires
            parent_window: Fenêtre parente pour la boîte de dialogue
            
        Returns:
            Tuple (succès, message)
        """
        try:
            # Vérifier si le point de montage existe, sinon le créer
            mount_path = Path(mount_point)
            if not mount_path.exists():
                try:
                    mount_path.mkdir(parents=True, exist_ok=True, mode=0o755)
                except Exception as e:
                    error_msg = f"Impossible de créer le répertoire de montage : {str(e)}"
                    logger.error(error_msg)
                    return False, error_msg
            
            # Préparer les options de montage
            mount_options = []
            
            # Ajouter les options spécifiées
            if options:
                mount_options.append(options)
            
            # Gérer les identifiants via un fichier sécurisé si un mot de passe est fourni
            if username and password:
                try:
                    # Créer un fichier d'identifiants temporaire
                    creds_file = self.credentials_manager.create_credentials_file(
                        username=username,
                        password=password,
                        domain=domain,
                        share_name=share,
                        server=server
                    )
                    
                    # Ajouter l'option credentials
                    mount_options.append(f"credentials={creds_file}")
                    
                    # Garder une trace du fichier de credentials pour le nettoyage
                    self.active_credentials[mount_point] = creds_file
                    
                except Exception as e:
                    logger.error("Erreur lors de la création du fichier d'identifiants : %s", str(e))
                    return False, f"Erreur de configuration des identifiants : {str(e)}"
            
            # Options par défaut pour CIFS si aucune option n'est spécifiée
            if filesystem.lower() == "cifs" and not options:
                default_opts = [
                    "vers=3.0",  # Version de SMB
                    "rw",        # Lecture/écriture
                    "nofail",    # Ne pas échouer au démarrage si le partage n'est pas disponible
                    "x-systemd.automount",  # Montage automatique avec systemd
                    "_netdev"    # Le partage nécessite un réseau
                ]
                mount_options.append(",".join(default_opts))
            
            # Construire la commande de montage
            cmd = ["mount", "-t", filesystem]
            
            # Ajouter les options combinées
            if mount_options:
                cmd.extend(["-o", ",".join(mount_options)])
            
            # Ajouter la source et la destination
            source = f"//{server}/{share}" if filesystem.lower() == "cifs" else f"{server}:{share}"
            cmd.extend([source, mount_point])
            
            # Journaliser la commande (sans le mot de passe)
            logger.info("Exécution de la commande : %s", " ".join(["sudo"] + cmd))
            
            # Exécuter la commande avec sudo
            success, output = self._run_sudo_command(cmd, parent_window)
            
            if success:
                logger.debug("Résultat du montage : %s", output)
                return True, f"Partage {share} monté avec succès sur {mount_point}"
            else:
                return False, output
                
        except Exception as e:
            error_msg = f"Erreur inattendue : {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
            
        except subprocess.CalledProcessError as e:
            return False, f"Échec du montage: {e.stderr}"
        except Exception as e:
            return False, f"Erreur inattendue: {str(e)}"
    
    def _is_mounted(self, mount_point: str) -> bool:
        """
        Vérifie si un point de montage est actuellement monté.
        
        Args:
            mount_point: Chemin du point de montage à vérifier
            
        Returns:
            bool: True si le point de montage est actuellement monté, False sinon
        """
        return os.path.ismount(mount_point)
    
    def _cleanup_credentials(self, mount_point: str) -> None:
        """
        Nettoie les fichiers d'identifiants temporaires pour un point de montage.
        
        Args:
            mount_point: Point de montage pour lequel nettoyer les identifiants
        """
        if mount_point in self.active_credentials:
            creds_file = self.active_credentials[mount_point]
            try:
                if os.path.exists(creds_file):
                    os.unlink(creds_file)
                    logger.debug("Fichier d'identifiants supprimé: %s", creds_file)
            except OSError as e:
                logger.error("Erreur lors de la suppression du fichier d'identifiants %s: %s", 
                           creds_file, e)
            finally:
                # Retirer la référence même en cas d'échec de suppression
                self.active_credentials.pop(mount_point, None)
    
    def unmount_share(
        self,
        mount_point: str,
        force: bool = False,
        lazy: bool = False,
        parent_window: Optional[tk.Tk] = None
    ) -> Tuple[bool, str]:
        """
        Démonte un partage réseau et nettoie les ressources associées.
        
        Args:
            mount_point: Point de montage à démonter
            force: Si True, force le démontage même en cas d'utilisation
            lazy: Si True, effectue un démontage paresseux (lazy unmount)
            parent_window: Fenêtre parente pour la boîte de dialogue
            
        Returns:
            Tuple (succès, message)
        """
        try:
            # Nettoyer et normaliser le chemin du point de montage
            mount_point = os.path.abspath(os.path.expanduser(mount_point.strip()))
            
            # Vérifier si le point de montage est effectivement monté
            if not self._is_mounted(mount_point):
                return False, f"Aucun système de fichiers n'est monté sur {mount_point}"
            
            # Construire la commande de démontage
            cmd = ["umount"]
            
            # Ajouter les options de démontage
            if force and not lazy:  # On ne peut pas combiner -f et -l
                cmd.append("-f")
                logger.info("Forçage du démontage de %s", mount_point)
            elif lazy:
                cmd.append("-l")
                logger.info("Démontage paresseux de %s", mount_point)
            
            # Ajouter le point de montage
            cmd.append(mount_point)
            
            logger.info("Exécution de la commande : sudo %s", " ".join(cmd))
            
            # Exécuter la commande avec sudo
            success, output = self._run_sudo_command(cmd, parent_window)
            
            if success:
                logger.info("Démontage réussi de %s", mount_point)
                
                # Nettoyer le fichier de credentials si nécessaire
                self._cleanup_credentials(mount_point)
                
                # Essayer de supprimer le répertoire de montage s'il est vide
                try:
                    mount_path = Path(mount_point)
                    if mount_path.exists() and not any(mount_path.iterdir()):
                        mount_path.rmdir()
                        logger.debug("Répertoire de montage supprimé : %s", mount_point)
                except Exception as e:
                    logger.warning("Impossible de supprimer le répertoire de montage : %s", str(e))
                
                return True, f"Partage démonté avec succès de {mount_point}"
            else:
                # En cas d'échec, essayer un démontage paresseux si ce n'était pas déjà le cas
                if not lazy and not success and "device is busy" in output.lower():
                    logger.info("Le périphérique est occupé, tentative de démontage paresseux...")
                    return self.unmount_share(mount_point, force=False, lazy=True, parent_window=parent_window)
                    
                error_msg = f"Échec du démontage de {mount_point}: {output}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Erreur inattendue lors du démontage : {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
    
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
