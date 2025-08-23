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
        Initialize an fstab entry.
        
        Args:
            filesystem: The filesystem or source (e.g., /dev/sda1 or //server/share)
            mount_point: The mount point (must be an absolute path)
            fs_type: The filesystem type (ext4, nfs, cifs, etc.)
            options: Mount options (comma-separated)
            dump: Backup option (usually 0 or 1)
            pass_num: Filesystem check order at boot (0, 1, or 2)
            comment: Optional comment
        """
        self.filesystem = filesystem.strip()
        self.mount_point = str(Path(mount_point).resolve())
        self.fs_type = fs_type.strip()
        self.options = options.strip()
        self.dump = int(dump)
        self.pass_num = int(pass_num)
        self.comment = comment.strip()
    
    def __str__(self) -> str:
        """Return the string representation of the fstab entry."""
        line = f"{self.filesystem} {self.mount_point} {self.fs_type} {self.options} {self.dump} {self.pass_num}"
        if self.comment:
            line = f"{line}  # {self.comment}"
        return line
    
    def __eq__(self, other: object) -> bool:
        """Compare two fstab entries, ignoring comments."""
        if not isinstance(other, FstabEntry):
            return False
        return (
            self.filesystem == other.filesystem and
            self.mount_point == other.mount_point and
            self.fs_type == other.fs_type
        )

class Fstab:
    """Class for manipulating the /etc/fstab file."""
    
    def __init__(self, fstab_path: str = "/etc/fstab"):
        """
        Initialize the fstab manager.
        
        Args:
            fstab_path: Path to the fstab file (default: /etc/fstab)
        """
        self.fstab_path = Path(fstab_path)
        self.entries: List[FstabEntry] = []
        self.load()
    
    def load(self) -> None:
        """Load the entries from the fstab file."""
        self.entries = []
        
        if not self.fstab_path.exists():
            raise FstabError(f"The file {self.fstab_path} does not exist")
        
        try:
            with open(self.fstab_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Ignore empty lines and comments
                    if not line or line.startswith('#'):
                        if line:
                            # Keep comments
                            self.entries.append(FstabEntry("", "", "", "", 0, 0, line.lstrip('#').strip()))
                        continue
                    
                    # Split the line into fields
                    parts = re.split(r'\s+', line, maxsplit=5)
                    if len(parts) < 6:
                        logger.warning("Malformed fstab line ignored: %s", line)
                        continue
                    
                    # Extract the fields
                    filesystem = parts[0]
                    mount_point = parts[1]
                    fs_type = parts[2]
                    options = parts[3]
                    
                    try:
                        dump = int(parts[4])
                        pass_num = int(parts[5].split('#')[0].strip())  # Remove comments
                    except (ValueError, IndexError):
                        logger.warning("Invalid numeric values in line: %s", line)
                        continue
                    
                    # Extract the comment if present
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
            raise FstabError(f"Failed to read the file {self.fstab_path}: {e}")
    
    def save(self, backup: bool = True) -> None:
        """
        Save the changes to the fstab file.
        
        Args:
            backup: If True, create a backup of the file before modification
        """
        if backup:
            backup_path = self.fstab_path.with_suffix(f".{self.fstab_path.suffix}.bak")
            try:
                shutil.copy2(self.fstab_path, backup_path)
                logger.info("Backup created: %s", backup_path)
            except IOError as e:
                raise FstabError(f"Failed to create a backup: {e}")
        
        # Generate the file content
        content = ""
        for entry in self.entries:
            if not entry.filesystem:  # It's a comment
                content += f"#{entry.comment}\n"
            else:
                content += f"{entry}\n"
        
        # Write the file securely
        secure_file_write(self.fstab_path, content, 0o644)
        logger.info("Fstab file updated: %s", self.fstab_path)
    
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
        Add an entry to the fstab file.
        
        Args:
            filesystem: The filesystem or source
            mount_point: The mount point
            fs_type: The filesystem type
            options: Mount options (default: "defaults")
            dump: Backup option (0 or 1)
            pass_num: Filesystem check order at boot (0, 1, or 2)
            comment: Optional comment
            check_duplicate: If True, check for duplicates before adding
            
        Returns:
            bool: True if the entry was added, False if it already exists
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
        
        # Check for duplicates
        if check_duplicate and new_entry in self.entries:
            logger.warning("Fstab entry already exists: %s", new_entry)
            return False
        
        self.entries.append(new_entry)
        return True
    
    def remove_entry(self, filesystem: str, mount_point: str, fs_type: str) -> bool:
        """
        Remove an entry from the fstab file.
        
        Args:
            filesystem: The filesystem or source
            mount_point: The mount point
            fs_type: The filesystem type
            
        Returns:
            bool: True if the entry was removed, False otherwise
        """
        target = FstabEntry(filesystem, mount_point, fs_type, "")
        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if e != target]
        return len(self.entries) < initial_count
    
    def find_entries_by_mount_point(self, mount_point: str) -> List[FstabEntry]:
        """
        Find all entries for a given mount point.
        
        Args:
            mount_point: Path to the mount point
            
        Returns:
            List of matching entries
        """
        mount_point = str(Path(mount_point).resolve())
        return [e for e in self.entries if e.mount_point == mount_point]
    
    def find_entries_by_filesystem(self, filesystem: str) -> List[FstabEntry]:
        """
        Find all entries for a given filesystem.
        
        Args:
            filesystem: The filesystem or source to search for
            
        Returns:
            List of matching entries
        """
        return [e for e in self.entries if e.filesystem == filesystem]
    
    def get_network_shares(self) -> List[FstabEntry]:
        """
        Get all network shares (NFS, CIFS, etc.).
        
        Returns:
            Liste des entrées de partage réseau
        """
        network_fs_types = ('nfs', 'nfs4', 'cifs', 'smb', 'smbfs')
        return [e for e in self.entries if e.fs_type.lower() in network_fs_types]
