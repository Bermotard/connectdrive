"""
Dialog for sudo password input.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple

class SudoPasswordDialog(tk.Toplevel):
    """Dialog for sudo password input."""
    
    def __init__(self, parent, title: str = "Authentication Required"):
        """Initialize the dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Variable to store the password
        self.password = tk.StringVar()
        self.result = None
        
        # Create the interface
        self._create_widgets()
        
        # Center the window on screen
        self._center_window()
        
        # Focus on the password field
        self.password_entry.focus_set()
    
    def _create_widgets(self) -> None:
        """Create the interface widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Information message
        message = "This operation requires administrative privileges.\nPlease enter your password:"
        ttk.Label(
            main_frame, 
            text=message,
            justify=tk.CENTER
        ).pack(pady=(0, 10))
        
        # Password field
        password_frame = ttk.Frame(main_frame)
        password_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(password_frame, text="Password:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.password_entry = ttk.Entry(
            password_frame, 
            textvariable=self.password, 
            show="•",
            width=30
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="OK", 
            command=self._on_ok,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
        
        # Event bindings
        self.password_entry.bind("<Return>", lambda e: self._on_ok())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_window(self) -> None:
        """Center the window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _on_ok(self) -> None:
        """Handle OK button event."""
        password = self.password.get().strip()
        if not password:
            messagebox.showwarning(
                "Missing Field",
                "Please enter your password.",
                parent=self
            )
            return
        
        self.result = password
        self.destroy()
    
    def _on_cancel(self) -> None:
        """Handle Cancel button event."""
        self.result = None
        self.destroy()
    
    @classmethod
    def ask_sudo_password(cls, parent, title: str = "Authentication Required") -> Optional[str]:
        """Show the dialog and return the entered password.
        
        Args:
            parent: Parent window
            title: Dialog title
            
        Returns:
            The entered password or None if cancelled
        """
        dialog = cls(parent, title)
        parent.wait_window(dialog)
        return dialog.result
