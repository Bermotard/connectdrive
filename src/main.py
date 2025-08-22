#!/usr/bin/env python3
"""
Point d'entrée principal de l'application Network Drive Mounter.
"""
import sys
import os
import tkinter as tk

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui.main_window import MainWindow

def main():
    """Lance l'application principale."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
