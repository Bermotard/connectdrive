"""
Boîte de dialogue pour gérer les identifiants de connexion.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from pathlib import Path
import os

class CredentialsDialog:
    """Boîte de dialogue pour gérer les identifiants de connexion."""
    
    def __init__(self, parent):
        """
        Initialise la boîte de dialogue.
        
        Args:
            parent: Fenêtre parente
        """
        self.parent = parent
        self.result = None
        
        # Créer la fenêtre modale
        self.top = tk.Toplevel(parent)
        self.top.title("Gestion des identifiants")
        self.top.geometry("500x300")
        self.top.resizable(False, False)
        
        # Centrer la fenêtre
        self._center_window()
        
        # Variables
        self.credentials = {
            'name': tk.StringVar(),
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'domain': tk.StringVar()
        }
        
        # Configuration de l'interface
        self._setup_ui()
        
        # Rendre la fenêtre modale
        self.top.transient(parent)
        self.top.grab_set()
        
        # Gestion de la fermeture de la fenêtre
        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_window(self) -> None:
        """Centre la fenêtre sur l'écran."""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'500x300+{x}+{y}')
    
    def _setup_ui(self) -> None:
        """Configure l'interface utilisateur."""
        # Frame principal
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formulaire
        form_frame = ttk.LabelFrame(main_frame, text="Nouveaux identifiants", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Champs du formulaire
        fields = [
            ("Nom:", "name"),
            ("Utilisateur:", "username"),
            ("Mot de passe:", "password", True),
            ("Domaine (optionnel):", "domain")
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
        
        # Configuration de la grille
        form_frame.columnconfigure(1, weight=1)
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            btn_frame, 
            text="Enregistrer", 
            command=self._on_save
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Annuler", 
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Raccourcis clavier
        self.top.bind('<Return>', lambda e: self._on_save())
        self.top.bind('<Escape>', lambda e: self._on_cancel())
    
    def _on_save(self) -> None:
        """Gère l'événement de sauvegarde."""
        # Vérifier les champs obligatoires
        if not all([self.credentials['name'].get(), 
                   self.credentials['username'].get(),
                   self.credentials['password'].get()]):
            messagebox.showerror(
                "Erreur",
                "Veuillez remplir tous les champs obligatoires (nom, utilisateur, mot de passe)"
            )
            return
        
        # Préparer le résultat
        self.result = {k: v.get() for k, v in self.credentials.items()}
        
        # Fermer la fenêtre
        self.top.destroy()
    
    def _on_cancel(self) -> None:
        """Gère l'événement d'annulation."""
        self.result = None
        self.top.destroy()
