#!/usr/bin/env python3
"""
Point d'entrée principal de l'application Network Drive Mounter.
"""
import tkinter as tk
from .gui.main_window import MainWindow

def main():
    """Lance l'application principale."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
