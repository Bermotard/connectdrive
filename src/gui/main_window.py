"""
Main window for the Network Drive Mounter application.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, Optional
import subprocess
import tempfile
import os

from ..config import settings
from .dialogs.credentials import CredentialsDialog
from .dialogs.purge_credentials_dialog import PurgeCredentialsDialog
from ..services.mount_service import MountService
from ..services.fstab_service import FstabService
from ..utils.logger import setup_logger

class MainWindow:
    """Main user interface class."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the main window."""
        self.root = root
        self.root.title(settings.APP_NAME)
        self.root.geometry(settings.DEFAULT_WINDOW_SIZE)
        self.root.minsize(*settings.MIN_WINDOW_SIZE)
        
        # Services
        self.mount_service = MountService()
        self.fstab_service = FstabService(parent_window=self.root)
        
        # Variables
        self.vars = {
            'server': tk.StringVar(),
            'share': tk.StringVar(),
            'mount_point': tk.StringVar(),
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'domain': tk.StringVar(),
            'filesystem': tk.StringVar(value=settings.DEFAULT_FILESYSTEM),
            'options': tk.StringVar(value=settings.DEFAULT_OPTIONS)
        }
        
        # Initialisation de l'interface
        self._setup_menu()
        self._setup_ui()
        self._setup_logging()
    
    def _setup_menu(self) -> None:
        """Configure the menu bar."""
        menubar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mount Points", command=self._list_mounts)
        
        # Fstab submenu
        fstab_menu = tk.Menu(file_menu, tearoff=0)
        fstab_menu.add_command(label="View", command=self._show_fstab)
        fstab_menu.add_command(label="Edit", command=self._edit_fstab)
        file_menu.add_cascade(label="fstab", menu=fstab_menu)
        
        # Credentials submenu
        creds_menu = tk.Menu(file_menu, tearoff=0)
        creds_menu.add_command(label="Manage Credentials", command=self._manage_credentials)
        creds_menu.add_command(label="Purge Unused Credentials", command=self._purge_credentials)
        file_menu.add_cascade(label="Credentials", menu=creds_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(
                self.tooltip, 
                text=text, 
                justify='left',
                background="#ffffe0",
                relief='solid',
                borderwidth=1,
                padding=5
            )
            label.pack()
        
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    
    def _setup_ui(self) -> None:
        """Configure the user interface."""
        # Button styles
        style = ttk.Style()
        style.configure('Warning.TButton', foreground='red')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection form
        self._setup_connection_form(main_frame)
        
        # Log area
        self._setup_log_area(main_frame)
        
        # Action buttons
        self._setup_action_buttons(main_frame)
    
    def _setup_connection_form(self, parent: ttk.Widget) -> None:
        """Configure the connection form."""
        form_frame = ttk.LabelFrame(parent, text="Connection Settings", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Field configuration
        fields = [
            ("Server:", "server"),
            ("Share:", "share"),
            ("Mount Point:", "mount_point"),
            ("Username:", "username"),
            ("Password:", "password", True),  # Password field
            ("Domain:", "domain"),
            ("Filesystem:", "filesystem"),
            ("Options:", "options")
        ]
        
        # Create fields
        for i, field in enumerate(fields):
            label_text, var_name, *rest = field
            is_password = bool(rest and rest[0])
            
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            entry = ttk.Entry(
                form_frame, 
                textvariable=self.vars[var_name],
                show="*" if is_password else ""
            )
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Grid configuration
        form_frame.columnconfigure(1, weight=1)
    
    def _setup_log_area(self, parent: ttk.Widget) -> None:
        """Configure the log area."""
        log_frame = ttk.LabelFrame(parent, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Text area with scrollbar
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame, 
            height=10, 
            wrap=tk.WORD, 
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
    
    def _setup_action_buttons(self, parent: ttk.Widget) -> None:
        """Configure the action buttons."""
        # Main button frame with padding
        main_btn_frame = ttk.Frame(parent, padding="10 10 10 10")
        main_btn_frame.pack(fill=tk.X, pady=10, padx=10, expand=True)
        
        # Main buttons
        buttons = [
            ("Mount", self._mount_share),
            ("Unmount", self._unmount_share),
            ("Add to fstab", self._add_to_fstab),
            ("Do Everything", self._do_everything)
        ]
        
        # Configure grid for main buttons
        main_btn_frame.columnconfigure(tuple(range(len(buttons))), weight=1, uniform='btn')
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(
                main_btn_frame, 
                text=text, 
                command=command,
                padding=5
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky=tk.NSEW)
        
        # Unmount options frame with more padding
        unmount_frame = ttk.LabelFrame(parent, text="Advanced Unmount Options", padding=10)
        unmount_frame.pack(fill=tk.X, pady=(0, 10), padx=10, ipady=5, before=main_btn_frame)  # Position above main buttons
        
        unmount_buttons = [
            ("Force Unmount", lambda: self._unmount_share(force=True)),
            ("Lazy Unmount", lambda: self._unmount_share(lazy=True))
        ]
        
        # Configure grid for unmount buttons
        unmount_frame.columnconfigure((0, 1), weight=1, uniform='unmount')
        
        for i, (text, command) in enumerate(unmount_buttons):
            btn = ttk.Button(
                unmount_frame,
                text=text,
                command=command,
                style="TButton",
                padding=5
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky=tk.NSEW)
            
            # Add tooltip
            tooltip = "Force unmount even if the device is busy" if i == 0 else \
                     "Unmount immediately but clean up references later"
            self._create_tooltip(btn, tooltip)
    
    def _setup_logging(self) -> None:
        """Configure the logging system."""
        self.logger = setup_logger()
    
    def _log(self, message: str) -> None:
        """Add a message to the log."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    # Action methods
    def _mount_share(self) -> None:
        """Mount the network share."""
        try:
            # Get parameters
            server = self.vars['server'].get().strip()
            share = self.vars['share'].get().strip()
            mount_point = self.vars['mount_point'].get().strip()
            username = self.vars['username'].get().strip()
            password = self.vars['password'].get()
            domain = self.vars['domain'].get().strip()
            filesystem = self.vars['filesystem'].get().strip()
            options = self.vars['options'].get().strip()
            
            # Validate required fields
            if not all([server, share, mount_point]):
                messagebox.showerror("Error", "Please fill in all required fields (server, share, mount point)")
                return
            
            self._log(f"Attempting to mount {server}/{share} on {mount_point}...")
            
            # Call mount service
            success, message = self.mount_service.mount_share(
                server=server,
                share=share,
                mount_point=mount_point,
                username=username or None,
                password=password or None,
                domain=domain or None,
                filesystem=filesystem or None,
                options=options or None,
                parent_window=self.root
            )
            
            if success:
                self._log(f"Success: {message}")
                messagebox.showinfo("Success", f"Share successfully mounted on {mount_point}")
            else:
                self._log(f"Failed: {message}")
                messagebox.showerror("Error", f"Mount failed: {message}")
            
        except Exception as e:
            error_msg = f"Error during mount: {str(e)}"
            self._log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _unmount_share(self, force: bool = False, lazy: bool = False) -> None:
        """
        Unmount the network share with the specified options.
        
        Args:
            force: If True, force unmount even if the device is busy
            lazy: If True, perform a lazy unmount (clean up references later)
        """
        try:
            mount_point = self.vars['mount_point'].get().strip()
            if not mount_point:
                messagebox.showerror("Error", "Please specify a mount point")
                return
            
            self._log(f"Attempting to unmount {mount_point}...")
            
            # Confirm with user if forcing or doing lazy unmount
            if force or lazy:
                options = []
                if force:
                    options.append("forced")
                if lazy:
                    options.append("lazy")
                
                confirm = messagebox.askyesno(
                    "Confirmation",
                    f"Are you sure you want to perform a {' and '.join(options)} unmount?\n\n"
                    "This operation may cause data loss if files are still in use.",
                    icon='warning'
                )
                if not confirm:
                    self._log("Unmount cancelled by user")
                    return
            
            # Call unmount service with options
            success, message = self.mount_service.unmount_share(
                mount_point=mount_point,
                force=force,
                lazy=lazy,
                parent_window=self.root
            )
            
            if success:
                self._log(f"Success: {message}")
                messagebox.showinfo("Success", f"Share successfully unmounted from {mount_point}")
            else:
                # Offer to force unmount if device is busy
                if not force and "device is busy" in message.lower():
                    retry = messagebox.askyesno(
                        "Device Busy",
                        f"Unable to unmount because the device is busy.\n\n"
                        "Would you like to force unmount?",
                        icon='warning'
                    )
                    if retry:
                        self._unmount_share(force=True, lazy=False)
                        return
                
                self._log(f"Failed: {message}")
                messagebox.showerror("Error", f"Unmount failed: {message}")
            
        except Exception as e:
            error_msg = f"Error during unmount: {str(e)}"
            self._log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _add_to_fstab(self) -> None:
        """Add entry to fstab."""
        try:
            # Get parameters
            server = self.vars['server'].get().strip()
            share = self.vars['share'].get().strip()
            mount_point = self.vars['mount_point'].get().strip()
            username = self.vars['username'].get().strip()
            password = self.vars['password'].get()
            domain = self.vars['domain'].get().strip()
            filesystem = self.vars['filesystem'].get().strip()
            options = self.vars['options'].get().strip()
            
            # Validate required fields
            if not all([server, share, mount_point]):
                messagebox.showerror("Error", "Server, Share, and Mount Point are required fields")
                return
                
            self._log(f"Adding {server}/{share} to fstab...")
            
            # Add to fstab
            success, message = self.fstab_service.add_fstab_entry(
                server=server,
                share=share,
                mount_point=mount_point,
                filesystem=filesystem,
                options=options,
                username=username or None,
                password=password or None,
                domain=domain or None
            )
            
            if success:
                self._log(f"Success: {message}")
                messagebox.showinfo("Success", "Entry successfully added to fstab")
            else:
                self._log(f"Failed: {message}")
                messagebox.showerror("Error", f"Failed to add to fstab: {message}")
                
        except Exception as e:
            error_msg = f"Error adding to fstab: {str(e)}"
            self._log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _do_everything(self) -> None:
        """Perform all actions (mount + fstab)."""
        self._mount_share()
        self._add_to_fstab()
    
    def _list_mounts(self) -> None:
        """Display the list of current mounts."""
        try:
            success, result = self.mount_service.list_mounts()
            if success:
                # Create a new window to display mounts
                window = tk.Toplevel(self.root)
                window.title("Active Mount Points")
                window.geometry("800x400")
                
                # Text area with scrollbar
                text = tk.Text(window, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(window, orient="vertical", command=text.yview)
                text.configure(yscrollcommand=scrollbar.set)
                
                # Display mounts
                text.insert(tk.END, "Active mount points:\n\n")
                text.insert(tk.END, result)
                text.config(state=tk.DISABLED)  # Read-only
                
                # Widget placement
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
                
                # Close button
                ttk.Button(
                    window, 
                    text="Close", 
                    command=window.destroy
                ).pack(pady=5)
                
                self._log("Mount points list displayed")
            else:
                messagebox.showerror("Error", f"Failed to list mounts: {result}")
                self._log(f"Error listing mounts: {result}")
                
        except Exception as e:
            error_msg = f"Error retrieving mounts: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self._log(error_msg)
    
    def _show_fstab(self) -> None:
        """Display the content of fstab."""
        try:
            success, content = self.fstab_service.read_fstab()
            if success:
                # Create a new window to display fstab
                window = tk.Toplevel(self.root)
                window.title("fstab Content")
                window.geometry("800x500")
                
                # Text area with scrollbar
                text = tk.Text(window, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(window, orient="vertical", command=text.yview)
                text.configure(yscrollcommand=scrollbar.set)
                
                # Display fstab content
                text.insert(tk.END, f"Content of {self.fstab_service.fstab_path}:\n\n")
                text.insert(tk.END, content)
                text.config(state=tk.DISABLED)  # Read-only
                
                # Widget placement
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
                
                # Close button
                ttk.Button(
                    window, 
                    text="Close", 
                    command=window.destroy
                ).pack(pady=5)
                
                self._log("fstab content displayed")
            else:
                messagebox.showerror("Error", f"Failed to read fstab: {content}")
                self._log(f"Error reading fstab: {content}")
                
        except Exception as e:
            error_msg = f"Error reading fstab: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self._log(error_msg)
    
    def _edit_fstab(self) -> None:
        """Open fstab in nano editor with sudo privileges in a new terminal window."""
        try:
            # Try to find a terminal emulator
            terminal_emulators = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'lxterminal', 'mate-terminal']
            terminal = None
            
            for term in terminal_emulators:
                if subprocess.run(['which', term], capture_output=True, text=True).returncode == 0:
                    terminal = term
                    break
            
            if not terminal:
                messagebox.showerror("Error", "No terminal emulator found. Please install one (e.g., gnome-terminal, konsole, xfce4-terminal)")
                return
            
            # Build the command based on the terminal emulator
            if terminal == 'gnome-terminal':
                cmd = [terminal, '--', 'sudo', '-e', 'nano', '/etc/fstab']
            elif terminal == 'konsole':
                cmd = [terminal, '-e', 'sudo nano /etc/fstab']
            elif terminal == 'x-terminal-emulator':
                cmd = [terminal, '-e', 'sudo nano /etc/fstab']
            else:
                cmd = [terminal, '-e', 'sudo nano /etc/fstab']
            
            # Execute the command
            subprocess.Popen(cmd, start_new_session=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open editor: {str(e)}")
    
    def _manage_credentials(self):
        """Open the credentials management dialog."""
        dialog = CredentialsDialog(self.root)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            self._log(f"Saved credentials for {dialog.result['name']}")
    
    def _purge_credentials(self):
        """Open the purge credentials dialog."""
        from .dialogs.purge_credentials_dialog import PurgeCredentialsDialog
        
        def on_purge_complete():
            self._log("Purged unused credentials")
        
        dialog = PurgeCredentialsDialog(
            self.root,
            self.mount_service.network_share_service if hasattr(self.mount_service, 'network_share_service') else self.mount_service,
            on_purge_complete=on_purge_complete
        )
        self.root.wait_window(dialog.top)
