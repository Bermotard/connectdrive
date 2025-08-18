#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import getpass

class NetworkMounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Monteur de lecteur réseau")
        self.root.geometry("600x600")
        self.root.minsize(550, 550)  # Taille minimale pour s'assurer que tout est visible
        
        # Variables
        self.server = tk.StringVar()
        self.share = tk.StringVar()
        self.mount_point = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.domain = tk.StringVar()
        self.filesystem = tk.StringVar(value="cifs")
        self.options = tk.StringVar(value="rw,user")
        
        # Interface utilisateur
        self.create_widgets()
    
    def create_widgets(self):
        # Cadre principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formulaire
        form_frame = ttk.LabelFrame(main_frame, text="Paramètres de connexion", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Champs du formulaire
        ttk.Label(form_frame, text="Serveur:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.server).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Partage:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.share).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Point de montage:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.mount_point).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Utilisateur:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.username).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Mot de passe:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.password, show="*").grid(row=4, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Domaine (optionnel):").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.domain).grid(row=5, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Options de montage
        options_frame = ttk.LabelFrame(main_frame, text="Options de montage", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(options_frame, text="Type de système de fichiers:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(options_frame, textvariable=self.filesystem, values=["cifs", "nfs"], state="readonly").grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(options_frame, text="Options:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(options_frame, textvariable=self.options).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Monter", command=self.mount_share).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ajouter à fstab", command=self.add_to_fstab).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tout faire", command=self.do_all).pack(side=tk.LEFT, padx=5)
        
        # Zone de journal avec ascenseur
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Ajout d'une barre de défilement
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Configurer la grille pour le redimensionnement
        form_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(1, weight=1)
    
    def log(self, message):
        """Ajoute un message au journal"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def get_sudo_password(self):
        """Affiche une boîte de dialogue pour saisir le mot de passe sudo"""
        if os.geteuid() == 0:  # Déjà root
            return True
            
        password_window = tk.Toplevel(self.root)
        password_window.title("Authentification requise")
        password_window.geometry("400x150")
        password_window.resizable(False, False)
        
        # Centrer la fenêtre
        window_width = 400
        window_height = 150
        screen_width = password_window.winfo_screenwidth()
        screen_height = password_window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        password_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        ttk.Label(password_window, text="Authentification requise pour monter le partage", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        password_var = tk.StringVar()
        ttk.Label(password_window, text="Mot de passe sudo:").pack(pady=5)
        password_entry = ttk.Entry(password_window, textvariable=password_var, show="*")
        password_entry.pack(pady=5, padx=20, fill=tk.X)
        password_entry.focus()
        
        result = {'password': None, 'ok': False}
        
        def on_ok():
            result['password'] = password_var.get()
            result['ok'] = True
            password_window.destroy()
            
        def on_cancel():
            password_window.destroy()
        
        button_frame = ttk.Frame(password_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Fermeture de la fenêtre avec la touche Entrée
        password_window.bind('<Return>', lambda e: on_ok())
        password_window.bind('<Escape>', lambda e: on_cancel())
        
        # Rendre la fenêtre modale
        password_window.transient(self.root)
        password_window.grab_set()
        self.root.wait_window(password_window)
        
        return result['password'] if result['ok'] else None

    def mount_share(self):
        """Monte le partage réseau"""
        server = self.server.get().strip()
        share = self.share.get().strip()
        mount_point = self.mount_point.get().strip()
        username = self.username.get().strip()
        password = self.password.get()
        domain = self.domain.get().strip()
        filesystem = self.filesystem.get()
        options = self.options.get().strip()
        
        # Demander le mot de passe sudo si nécessaire
        sudo_password = None
        if os.geteuid() != 0:
            sudo_password = self.get_sudo_password()
            if sudo_password is None:
                self.log("Opération annulée par l'utilisateur")
                return False
        
        if not all([server, share, mount_point]):
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs obligatoires")
            return
        
        # Créer le point de montage s'il n'existe pas
        if not os.path.exists(mount_point):
            try:
                os.makedirs(mount_point, exist_ok=True)
                self.log(f"Point de montage créé: {mount_point}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer le point de montage: {e}")
                return
        
        # Construire la commande mount
        source = f"//{server}/{share}" if filesystem == "cifs" else f"{server}:{share}"
        mount_cmd = ["sudo", "mount", "-t", filesystem]
        
        # Ajouter les options d'authentification pour CIFS
        if filesystem == "cifs":
            creds = []
            if username:
                creds.append(f"username={username}")
            if password:
                creds.append(f"password={password}")
            if domain:
                creds.append(f"domain={domain}")
            
            if creds:
                creds_str = ",".join(creds)
                mount_cmd.extend(["-o", f"{options},{creds_str}"])
            elif options:
                mount_cmd.extend(["-o", options])
        elif options:
            mount_cmd.extend(["-o", options])
        
        mount_cmd.extend([source, mount_point])
        
        # Exécuter la commande
        try:
            self.log(f"Exécution de la commande: {' '.join(mount_cmd)}")
            # Préparer l'entrée pour sudo si nécessaire
            process_input = None
            if os.geteuid() != 0 and sudo_password:
                process_input = f"{sudo_password}\n"
                
            result = subprocess.run(
                mount_cmd,
                capture_output=True,
                text=True,
                input=process_input
            )
            
            if result.returncode == 0:
                self.log("Montage réussi!")
                messagebox.showinfo("Succès", "Le partage a été monté avec succès!")
                return True
            else:
                error_msg = f"Erreur lors du montage: {result.stderr}"
                self.log(error_msg)
                messagebox.showerror("Erreur", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution de la commande: {e}"
            self.log(error_msg)
            messagebox.showerror("Erreur", error_msg)
            return False
    
    def add_to_fstab(self):
        """Ajoute une entrée dans /etc/fstab"""
        server = self.server.get().strip()
        share = self.share.get().strip()
        mount_point = self.mount_point.get().strip()
        username = self.username.get().strip()
        password = self.password.get()
        domain = self.domain.get().strip()
        filesystem = self.filesystem.get()
        options = self.options.get().strip()
        
        if not all([server, share, mount_point]):
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs obligatoires")
            return False
        
        # Construire la ligne fstab
        source = f"//{server}/{share}" if filesystem == "cifs" else f"{server}:{share}"
        
        # Préparer les options pour fstab
        fstab_options = options
        if filesystem == "cifs":
            creds = []
            if username:
                creds.append(f"username={username}")
            if password:
                # Note: Stocker le mot de passe en clair dans fstab n'est pas sécurisé
                # Une meilleure approche serait d'utiliser un fichier d'identifiants
                creds.append(f"password={password}")
            if domain:
                creds.append(f"domain={domain}")
            
            if creds:
                fstab_options = f"{options},{','.join(creds)}" if options else ",".join(creds)
        
        fstab_line = f"{source}\t{mount_point}\t{filesystem}\t{fstab_options}\t0 0\n"
        
        try:
            # Sauvegarder l'ancien fstab
            with open("/etc/fstab", "r") as f:
                fstab_content = f.read()
            
            # Vérifier si l'entrée existe déjà
            if f"{mount_point}" in fstab_content:
                messagebox.showwarning("Attention", f"Une entrée pour {mount_point} existe déjà dans fstab.")
                return False
            
            # Ajouter la nouvelle entrée
            with open("/etc/fstab", "a") as f:
                f.write(fstab_line)
            
            self.log(f"Entrée ajoutée à /etc/fstab:")
            self.log(fstab_line.strip())
            messagebox.showinfo("Succès", "L'entrée a été ajoutée à /etc/fstab")
            return True
            
        except PermissionError:
            # Essayer avec sudo
            try:
                cmd = ["sudo", "sh", "-c", f"echo '{fstab_line}' >> /etc/fstab"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log(f"Entrée ajoutée à /etc/fstab:")
                    self.log(fstab_line.strip())
                    messagebox.showinfo("Succès", "L'entrée a été ajoutée à /etc/fstab")
                    return True
                else:
                    error_msg = f"Erreur lors de l'ajout à fstab: {result.stderr}"
                    self.log(error_msg)
                    messagebox.showerror("Erreur", error_msg)
                    return False
                    
            except Exception as e:
                error_msg = f"Erreur lors de l'ajout à fstab: {e}"
                self.log(error_msg)
                messagebox.showerror("Erreur", error_msg)
                return False
    
    def do_all(self):
        """Exécute toutes les opérations"""
        if self.mount_share():
            self.add_to_fstab()

def main():
    root = tk.Tk()
    app = NetworkMounter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
