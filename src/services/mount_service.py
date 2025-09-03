"""
Service to manage mounting and unmounting network shares.
"""
import subprocess
import shlex
import os
import pwd
import grp
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
        try:
            # Check if we're already root
            if os.geteuid() == 0:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return True, result.stdout
            else:
                # Ask for sudo password
                if parent_window is None:
                    parent_window = tk.Tk()
                    parent_window.withdraw()
                
                password = SudoPasswordDialog.ask_sudo_password(parent_window)
                if password is None:
                    return False, "Sudo password required"
                
                # Run command with sudo
                sudo_cmd = ["sudo", "-S"] + command
                result = subprocess.run(
                    sudo_cmd,
                    input=password,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return True, result.stdout
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with error: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg

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
        Mount a network share.
        
        Args:
            server: Server address
            share: Share name
            mount_point: Local mount point
            username: Username for authentication
            password: Password for authentication
            domain: Domain for authentication
            filesystem: Filesystem type (default: cifs)
            options: Additional mount options
            parent_window: Parent window for dialogs
            
        Returns:
            Tuple (success, message)
        """
        try:
            # Create mount point if it doesn't exist
            try:
                os.makedirs(mount_point, exist_ok=True)
                # Set correct permissions (read/write/execute for owner, read/execute for group/others)
                os.chmod(mount_point, 0o755)
                logger.debug(f"Created mount point directory: {mount_point}")
            except Exception as e:
                error_msg = f"Failed to create mount point {mount_point}: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
            
            # Prepare mount options
            current_user = pwd.getpwuid(os.getuid())
            current_group = grp.getgrgid(current_user.pw_gid)
            mount_options = [
                f"uid={current_user.pw_uid}",
                f"gid={current_user.pw_gid}",
                "file_mode=0777",
                "dir_mode=0777"
            ]
            
            # Add username and password if provided
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
            
            # Add force option to handle existing mount points
            cmd.append("-o")
            cmd.append("nofail")
            cmd.extend([source, mount_point])
            
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
            parent_window: Parent window for dialogs
            
        Returns:
            Tuple (success, message)
        """
        try:
            if not os.path.ismount(mount_point):
                return False, f"{mount_point} is not a mount point"
            
            # Build the unmount command
            cmd = ["umount"]
            
            if force:
                cmd.append("-f")
            if lazy:
                cmd.append("-l")
                
            cmd.append(mount_point)
            
            # Execute the command with sudo
            success, output = self._run_sudo_command(cmd, parent_window)
            
            if success:
                logger.info("Unmount successful: %s", mount_point)
                # Clean up credential files if they exist
                self._cleanup_credentials(mount_point)
                return True, f"Successfully unmounted {mount_point}"
            else:
                return False, output
                
        except Exception as e:
            error_msg = f"Error during unmount: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg

    def _cleanup_credentials(self, mount_point: str) -> None:
        """
        Clean up credentials file for a mount point.
        
        Args:
            mount_point: Path of the mount point
        """
        if mount_point in self.active_credentials:
            creds_file = self.active_credentials[mount_point]
            try:
                if os.path.exists(creds_file):
                    os.unlink(creds_file)
                    logger.debug("Credentials file deleted: %s", creds_file)
            except OSError as e:
                logger.warning("Error deleting credentials file: %s", str(e))
            finally:
                # Remove the reference even if deletion failed
                self.active_credentials.pop(mount_point, None)

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
