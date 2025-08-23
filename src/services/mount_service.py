"""
Service to manage mounting and unmounting network shares.
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
    """Service to manage mounting operations."""
    
    def __init__(self):
        """Initialize the mount service with the credentials manager."""
        from .network_share import NetworkShareService
        self.credentials_manager = CredentialsManager()
        self.active_credentials = {}  # To keep track of active credential files
        self.network_share_service = NetworkShareService()

    def _run_sudo_command(self, command: List[str], parent_window: Optional[tk.Tk] = None) -> Tuple[bool, str]:
        """
        Execute a command with sudo, asking for password if needed.
        
        Args:
            command: Command to execute
            parent_window: Parent window for the dialog
            
        Returns:
            Tuple (success, output or error message)
        """
        # Ask for sudo password
        if parent_window is None:
            parent_window = tk.Tk()
            parent_window.withdraw()  # Hide the root window
        
        password = SudoPasswordDialog.ask_sudo_password(parent_window)
        if password is None:
            return False, "Authentication cancelled by user"
        
        # Create a temporary file for the password
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write(f"{password}\n")
            temp_file = f.name
        
        try:
            # Set file permissions
            os.chmod(temp_file, 0o600)
            
            # Build the command with sudo -S to read password from stdin
            sudo_cmd = ["sudo", "-S"] + command
            
            # Execute the command
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
                error_msg = result.stderr or f"Command failed (code {result.returncode})"
                logger.error("Execution error: %s", error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Command execution timed out"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning("Could not delete temporary file: %s", str(e))
    
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
        Mount a network share using a credentials file for security.
        
        Args:
            server: Server address
            share: Share name
            mount_point: Local mount point
            username: Username (optional)
            password: Password (optional, can contain special characters)
            domain: Domain (optional)
            filesystem: Filesystem type (default: cifs)
            options: Additional mount options
            parent_window: Parent window for the dialog
            
        Returns:
            Tuple (success, message)
        """
        try:
            # Check if mount point exists, create it if not
            mount_path = Path(mount_point)
            if not mount_path.exists():
                try:
                    mount_path.mkdir(parents=True, exist_ok=True, mode=0o755)
                except Exception as e:
                    error_msg = f"Could not create mount directory: {str(e)}"
                    logger.error(error_msg)
                    return False, error_msg
            
            # Prepare mount options
            mount_options = []
            
            # Add specified options
            if options:
                mount_options.append(options)
            
            # Handle credentials via secure file if password is provided
            if username and password:
                try:
                    # Create temporary credentials file
                    creds_file = self.credentials_manager.create_credentials_file(
                        username=username,
                        password=password,
                        domain=domain,
                        share_name=share,
                        server=server
                    )
                    
                    # Add credentials option
                    mount_options.append(f"credentials={creds_file}")
                    
                    # Keep track of credentials file for cleanup
                    self.active_credentials[mount_point] = creds_file
                    
                except Exception as e:
                    logger.error("Error creating credentials file: %s", str(e))
                    return False, f"Error configuring credentials: {str(e)}"
            
            # Default options for CIFS if no options specified
            if filesystem.lower() == "cifs" and not options:
                default_opts = [
                    "vers=3.0",  # SMB version
                    "rw",        # Read/write
                    "nofail",    # Don't fail on boot if share is unavailable
                    "x-systemd.automount",  # Automatic mounting with systemd
                    "_netdev"    # Share requires network
                ]
                mount_options.append(",".join(default_opts))
            
            # Build the mount command
            cmd = ["mount", "-t", filesystem]
            
            # Add combined options
            if mount_options:
                cmd.extend(["-o", ",".join(mount_options)])
            
            # Add source and destination
            source = f"//{server}/{share}" if filesystem.lower() == "cifs" else f"{server}:{share}"
            cmd.extend([source, mount_point])
            
            # Log the command (without password)
            logger.info("Executing command: %s", " ".join(["sudo"] + cmd))
            
            # Execute the command with sudo
            success, output = self._run_sudo_command(cmd, parent_window)
            
            if success:
                logger.debug("Mount result: %s", output)
                return True, f"Share {share} successfully mounted on {mount_point}"
            else:
                return False, output
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
            
        except subprocess.CalledProcessError as e:
            return False, f"Mount failed: {e.stderr}"
    
    def _is_mounted(self, mount_point: str) -> bool:
        """
        Check if a mount point is currently mounted.
        
        Args:
            mount_point: Path of the mount point to check
            
        Returns:
            bool: True if the mount point is active, False otherwise
        """
        return os.path.ismount(mount_point)
    
    def _cleanup_credentials(self, mount_point: str) -> None:
        """
{{ ... }}
        if mount_point in self.active_credentials:
            creds_file = self.active_credentials[mount_point]
            try:
                if os.path.exists(creds_file):
                    os.unlink(creds_file)
                    logger.debug("Credentials file deleted: %s", creds_file)
            except OSError as e:
                logger.warning("Error deleting credentials file: %s", str(e))
            finally:
                # Remove the reference even in case of deletion failure
                self.active_credentials.pop(mount_point, None)
    
    def unmount_share(
        self,
        mount_point: str,
        force: bool = False,
        lazy: bool = False,
        parent_window: Optional[tk.Tk] = None
    ) -> Tuple[bool, str]:
        """
        Unmount a mounted network share.
        
        Args:
            mount_point: Path of the mount point to unmount
            force: If True, force the unmount even if the device is busy
            lazy: If True, performs a lazy unmount
            parent_window: Parent window for the dialog
            
        Returns:
            Tuple (success, message)
        """
{{ ... }}
            success, output = self._run_sudo_command(cmd, parent_window)
            
            if success:
                logger.info("Unmount successful: %s", mount_point)
                
                # Clean up credential files if needed
                self._cleanup_credentials(mount_point)
                
                # Try to delete the mount directory if it is empty
                try:
                    mount_path = Path(mount_point)
                    if mount_path.exists() and not any(mount_path.iterdir()):
                        mount_path.rmdir()
                        logger.debug("Mount directory deleted: %s", mount_point)
                except Exception as e:
                    logger.warning("Failed to delete mount directory: %s", str(e))
                
                return True, f"Share successfully unmounted: {mount_point}"
            else:
                # In case of failure, try a lazy unmount if not already done
                if not lazy and not success and "device is busy" in output.lower():
                    logger.info("Device is busy, attempting lazy unmount...")
                    return self.unmount_share(mount_point, force=False, lazy=True, parent_window=parent_window)
                    
                error_msg = f"Unmount failed: {output}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error during unmount: {str(e)}"
{{ ... }}
            return False, error_msg
    
    def list_mounts(self) -> Tuple[bool, str]:
        """
        List active mount points.
        
        Returns:
            Tuple (success, result or error message)
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
            return False, f"Failed to list mount points: {e.stderr}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
