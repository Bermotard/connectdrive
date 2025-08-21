"""
Dialog for managing connection credentials.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from pathlib import Path
import os

class CredentialsDialog:
    """Dialog for managing connection credentials."""
    
    def __init__(self, parent):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        self.result = None
        
        # Create the modal window
        self.top = tk.Toplevel(parent)
        self.top.title("Credentials Management")
        self.top.geometry("500x300")
        self.top.resizable(False, False)
        
        # Center the window
        self._center_window()
        
        # Variables
        self.credentials = {
            'name': tk.StringVar(),
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'domain': tk.StringVar()
        }
        
        # UI Setup
        self._setup_ui()
        
        # Make the window modal
        self.top.transient(parent)
        self.top.grab_set()
        
        # Handle window close
        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_window(self) -> None:
        """Center the window on the screen."""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'500x300+{x}+{y}')
    
    def _setup_ui(self) -> None:
        """Configure the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form
        form_frame = ttk.LabelFrame(main_frame, text="New Credentials", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Form fields
        fields = [
            ("Name:", "name"),
            ("Username:", "username"),
            ("Password:", "password", True),
            ("Domain (optional):", "domain")
        ]
        
        for i, field in enumerate(fields):
            label_text, var_name, *rest = field
            is_password = bool(rest and rest[0])
            
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            entry = ttk.Entry(
                form_frame, 
                textvariable=self.credentials[var_name],
                show="*" if is_password else ""
            )
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Grid configuration
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            btn_frame, 
            text="Save", 
            command=self._on_save
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Cancel", 
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Keyboard shortcuts
        self.top.bind('<Return>', lambda e: self._on_save())
        self.top.bind('<Escape>', lambda e: self._on_cancel())
    
    def _on_save(self) -> None:
        """Handle save event."""
        # Check required fields
        if not all([self.credentials['name'].get(), 
                   self.credentials['username'].get(),
                   self.credentials['password'].get()]):
            messagebox.showerror(
                "Error",
                "Please fill in all required fields (name, username, password)"
            )
            return
        
        # Prepare the result
        self.result = {k: v.get() for k, v in self.credentials.items()}
        
        # Close the window
        self.top.destroy()
    
    def _on_cancel(self) -> None:
        """Handle cancel event."""
        self.result = None
        self.top.destroy()
