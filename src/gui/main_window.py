"""
Fenêtre principale de l'application Network Drive Mounter.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from ..config import settings
from .dialogs.credentials import CredentialsDialog
from ..services.mount_service import MountService
from ..services.fstab_service import FstabService
from ..utils.logger import setup_logger

class MainWindow:
    """Classe principale de l'interface utilisateur."""
    
    def __init__(self, root: tk.Tk):
        """Initialise la fenêtre principale."""
        self.root = root
        self.root.title(settings.APP_NAME)
        self.root.geometry(settings.DEFAULT_WINDOW_SIZE)
        self.root.minsize(*settings.MIN_WINDOW_SIZE)
        
        # Services
        self.mount_service = MountService()
        self.fstab_service = FstabService()
        
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
        """Configure la barre de menus."""
        menubar = tk.Menu(self.root)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Liste des montages", command=self._list_mounts)
        file_menu.add_command(label="Voir fstab", command=self._show_fstab)
        file_menu.add_command(label="Gérer les identifiants", command=self._manage_credentials)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        menubar.add_cascade(label="Fichier", menu=file_menu)
        self.root.config(menu=menubar)
    
    def _setup_ui(self) -> None:
        """Configure l'interface utilisateur."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formulaire de connexion
        self._setup_connection_form(main_frame)
        
        # Zone de logs
        self._setup_log_area(main_frame)
        
        # Boutons d'action
        self._setup_action_buttons(main_frame)
    
    def _setup_connection_form(self, parent: ttk.Widget) -> None:
        """Configure le formulaire de connexion."""
        form_frame = ttk.LabelFrame(parent, text="Paramètres de connexion", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Configuration des champs
        fields = [
            ("Serveur:", "server"),
            ("Partage:", "share"),
            ("Point de montage:", "mount_point"),
            ("Utilisateur:", "username"),
            ("Mot de passe:", "password", True),  # Champ de mot de passe
            ("Domaine:", "domain"),
            ("Système de fichiers:", "filesystem"),
            ("Options:", "options")
        ]
        
        # Création des champs
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
        
        # Configuration de la grille
        form_frame.columnconfigure(1, weight=1)
    
    def _setup_log_area(self, parent: ttk.Widget) -> None:
        """Configure la zone de logs."""
        log_frame = ttk.LabelFrame(parent, text="Journal", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Zone de texte avec ascenseur
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
        """Configure les boutons d'action."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)
        
        buttons = [
            ("Monter", self._mount_share),
            ("Démonter", self._unmount_share),
            ("Ajouter à fstab", self._add_to_fstab),
            ("Tout faire", self._do_everything)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(
                btn_frame, 
                text=text, 
                command=command
            ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def _setup_logging(self) -> None:
        """Configure le système de journalisation."""
        self.logger = setup_logger()
    
    def _log(self, message: str) -> None:
        """Ajoute un message au journal."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    # Méthodes des actions
    def _mount_share(self) -> None:
        """Monte le partage réseau."""
        try:
            mount_point = self.vars['mount_point'].get().strip()
            if not mount_point:
                messagebox.showerror("Erreur", "Veuillez spécifier un point de montage")
                return
            
            self._log(f"Montage du partage sur {mount_point}...")
            # Implémentation du montage...
            
        except Exception as e:
            self._log(f"Erreur lors du montage: {str(e)}")
    
    def _unmount_share(self) -> None:
        """Démonte le partage réseau."""
        try:
            mount_point = self.vars['mount_point'].get().strip()
            if not mount_point:
                messagebox.showerror("Erreur", "Veuillez spécifier un point de montage")
                return
            
            self._log(f"Démontage de {mount_point}...")
            # Implémentation du démontage...
            
        except Exception as e:
            self._log(f"Erreur lors du démontage: {str(e)}")
    
    def _add_to_fstab(self) -> None:
        """Ajoute l'entrée à fstab."""
        self._log("Ajout à fstab...")
        # Implémentation de l'ajout à fstab...
    
    def _do_everything(self) -> None:
        """Effectue toutes les actions (montage + fstab)."""
        self._mount_share()
        self._add_to_fstab()
    
    def _list_mounts(self) -> None:
        """Affiche la liste des points de montage actifs."""
        self._log("Liste des points de montage...")
        # Implémentation de la liste des montages...
    
    def _show_fstab(self) -> None:
        """Affiche le contenu du fichier fstab."""
        self._log("Affichage du fichier fstab...")
        # Implémentation de l'affichage de fstab...
    
    def _manage_credentials(self) -> None:
        """Ouvre la boîte de dialogue de gestion des identifiants."""
        dialog = CredentialsDialog(self.root)
        self.root.wait_window(dialog.top)
        if dialog.result:
            self._log("Identifiants enregistrés")

