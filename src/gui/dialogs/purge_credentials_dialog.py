"""
Dialog for managing and purging unused credentials.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime

class PurgeCredentialsDialog:
    """Dialog for displaying and purging unused credentials."""
    
    def __init__(self, parent, network_share_service, on_purge_complete: Optional[Callable] = None):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent window
            network_share_service: Instance of NetworkShareService
            on_purge_complete: Callback function to execute after purging credentials
        """
        self.parent = parent
        self.network_share_service = network_share_service
        self.on_purge_complete = on_purge_complete
        self.selected_credentials = set()
        
        # Create the modal window
        self.top = tk.Toplevel(parent)
        self.top.title("Purge Unused Credentials")
        self.top.geometry("800x500")
        self.top.resizable(True, True)
        self.top.minsize(700, 400)
        
        # Center the window
        self._center_window()
        
        # Setup UI
        self._setup_ui()
        
        # Load credentials
        self.refresh_credentials()
        
        # Make the window modal
        self.top.transient(parent)
        self.top.grab_set()
        
        # Handle window close
        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_window(self):
        """Center the window on the screen."""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.top, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame, 
            text="Unused Credentials",
            font=('Helvetica', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        # Buttons frame
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self.refresh_credentials,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        self.purge_btn = ttk.Button(
            btn_frame,
            text="Purge Selected",
            command=self.purge_selected,
            width=15,
            state=tk.DISABLED
        )
        self.purge_btn.pack(side=tk.LEFT, padx=5)
        
        # Treeview for credentials
        self._setup_treeview(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        ).pack(fill=tk.X, pady=(10, 0))
    
    def _setup_treeview(self, parent):
        """Set up the treeview for displaying credentials."""
        # Create a frame for the treeview and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a treeview with scrollbars
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('username', 'domain', 'file', 'size', 'modified'),
            show='headings',
            selectmode='extended'
        )
        
        # Configure the columns
        self.tree.heading('username', text='Username', anchor=tk.W)
        self.tree.heading('domain', text='Domain', anchor=tk.W)
        self.tree.heading('file', text='File', anchor=tk.W)
        self.tree.heading('size', text='Size', anchor=tk.CENTER)
        self.tree.heading('modified', text='Modified', anchor=tk.W)
        
        # Set column widths
        self.tree.column('username', width=150, minwidth=100, stretch=tk.NO)
        self.tree.column('domain', width=100, minwidth=80, stretch=tk.NO)
        self.tree.column('file', width=200, minwidth=150)
        self.tree.column('size', width=80, minwidth=60, stretch=tk.NO, anchor=tk.E)
        self.tree.column('modified', width=150, minwidth=120, stretch=tk.NO)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_change)
    
    def _on_selection_change(self, event):
        """Handle selection change in the treeview."""
        selected_items = self.tree.selection()
        self.purge_btn['state'] = tk.NORMAL if selected_items else tk.DISABLED
    
    def refresh_credentials(self):
        """Refresh the list of unused credentials."""
        self.status_var.set("Loading unused credentials...")
        self.top.update()
        
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get unused credentials
            unused_creds = self.network_share_service.find_unused_credentials()
            
            if not unused_creds:
                self.status_var.set("No unused credentials found.")
                return
            
            # Add credentials to treeview
            for cred in unused_creds:
                # Format size
                size = self._format_size(cred['size'])
                
                # Format modification time
                mtime = datetime.fromtimestamp(cred['mtime']).strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert into treeview
                self.tree.insert(
                    '', 'end',
                    values=(
                        cred['username'],
                        cred['domain'] or '-',
                        cred['file'],
                        size,
                        mtime
                    ),
                    tags=('unused',)
                )
            
            self.status_var.set(f"Found {len(unused_creds)} unused credentials.")
            
        except Exception as e:
            self.status_var.set("Error loading credentials.")
            messagebox.showerror("Error", f"Failed to load credentials: {str(e)}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def purge_selected(self):
        """Purge the selected credentials."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Confirm before deletion
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_items)} selected credential files?\n"
            "This action cannot be undone."
        ):
            return
        
        # Delete selected credentials
        deleted = 0
        errors = 0
        
        for item in selected_items:
            values = self.tree.item(item, 'values')
            if not values:
                continue
                
            file_path = Path(self.network_share_service.credentials_manager.credentials_dir) / values[2]  # filename is at index 2
            
            try:
                if self.network_share_service.credentials_manager.delete_credentials_file(file_path):
                    self.tree.delete(item)
                    deleted += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                logger.error(f"Error deleting {file_path}: {e}")
        
        # Update status
        if deleted > 0:
            self.status_var.set(f"Successfully deleted {deleted} credential(s)." + 
                              (f" {errors} error(s) occurred." if errors > 0 else ""))
            
            # Call the completion callback if provided
            if self.on_purge_complete:
                self.on_purge_complete()
        else:
            self.status_var.set("No credentials were deleted." + 
                              (f" {errors} error(s) occurred." if errors > 0 else ""))
    
    def _on_cancel(self):
        """Handle window close event."""
        self.top.destroy()
