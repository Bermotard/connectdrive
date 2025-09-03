#!/usr/bin/env python3
"""
Main entry point for the Network Drive Mounter application. V0.9.2
"""
import sys
import os
import tkinter as tk

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui.main_window import MainWindow
from src.gui.styles.style import apply_styles

def main():
    """Launch the main application."""
    root = tk.Tk()
    
    # Apply custom styles
    style = apply_styles(root)
    
    # Set application icon if available
    try:
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Could not load application icon: {e}")
    
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
