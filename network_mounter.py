#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import getpass

class NetworkMounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Drive Mounter")
        self.root.geometry("600x600")
        self.root.minsize(550, 550)  # Minimum size to ensure everything is visible
        
        # Variables
        self.server = tk.StringVar()
        self.share = tk.StringVar()
        self.mount_point = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.domain = tk.StringVar()
        self.filesystem = tk.StringVar(value="cifs")
        self.options = tk.StringVar(value="rw,user")
        
        # Create menu
        self.create_menu()
        
        # Create user interface
        self.create_widgets()
    
    def create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="List Mounts", command=self.list_mounts)
        file_menu.add_command(label="Display fstab", command=self.display_fstab)
        file_menu.add_command(label="Create Credential File", command=self.create_credential_file)
        file_menu.add_command(label="Console", command=self.show_console)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
    
    def display_fstab(self):
        """Display the content of /etc/fstab in a new window"""
        try:
            with open('/etc/fstab', 'r') as f:
                fstab_content = f.read()
            
            fstab_window = tk.Toplevel(self.root)
            fstab_window.title("fstab Content")
            fstab_window.geometry("800x600")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(fstab_window)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add text widget for fstab content
            text_widget = tk.Text(fstab_window, wrap=tk.WORD, yscrollcommand=scrollbar.set)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Insert fstab content
            text_widget.insert(tk.END, fstab_content)
            text_widget.config(state=tk.DISABLED)  # Make it read-only
            
            # Configure scrollbar
            scrollbar.config(command=text_widget.yview)
            
            # Make the window resizable
            fstab_window.resizable(True, True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read /etc/fstab: {str(e)}")
    
    def show_console(self):
        """Show the console window with application logs"""
        console_window = tk.Toplevel(self.root)
        console_window.title("Application Console")
        console_window.geometry("800x400")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(console_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add text widget for logs
        console_text = tk.Text(console_window, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Insert current log content
        console_text.insert(tk.END, self.log_text.get("1.0", tk.END))
        console_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Configure scrollbar
        scrollbar.config(command=console_text.yview)
        
        # Make the window resizable
        console_window.resizable(True, True)
        
        # Set focus to the console window
        console_window.focus_set()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formulaire
        form_frame = ttk.LabelFrame(main_frame, text="Connection Settings", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Champs du formulaire
        ttk.Label(form_frame, text="Server:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.server).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Share:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.share).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Mount Point:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.mount_point).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Username:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.username).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Password:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.password, show="*").grid(row=4, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Domain (optional):").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.domain).grid(row=5, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Options de montage
        options_frame = ttk.LabelFrame(main_frame, text="Mount Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(options_frame, text="Filesystem Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(options_frame, textvariable=self.filesystem, values=["cifs", "nfs"], state="readonly").grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(options_frame, text="Options:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(options_frame, textvariable=self.options).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Mount", command=self.mount_share).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add to fstab", command=self.add_to_fstab).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Do Everything", command=self.do_all).pack(side=tk.LEFT, padx=5)
        
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
    
    def populate_fields_from_mount(self, mount_info, window):
        """Populate form fields from selected mount info"""
        try:
            # Parse mount info (example: //server/share on /mnt/point type cifs (...)
            parts = mount_info.split()
            if len(parts) >= 3:
                source = parts[0]
                mount_point = parts[2]
                
                # Extract server and share from source (//server/share)
                if source.startswith('//'):
                    server_share = source[2:].split('/')
                    if len(server_share) >= 2:
                        self.server.set(server_share[0])
                        self.share.set('/'.join(server_share[1:]))
                        self.mount_point.set(mount_point)
                        
                        # Try to find username in options
                        options = ' '.join(parts[3:]) if len(parts) > 3 else ''
                        if 'username=' in options:
                            self.username.set(options.split('username=')[1].split(',')[0].strip('\"\''))
                        if 'domain=' in options:
                            self.domain.set(options.split('domain=')[1].split(',')[0].strip('\"\''))
                        
                        # Set filesystem type
                        if len(parts) >= 5 and parts[4] == 'type':
                            self.filesystem.set(parts[5])
                        
                        window.destroy()
                        return
            
            messagebox.showinfo("Info", "Could not parse all mount information. Some fields may be empty.")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse mount info: {str(e)}")
    
    def list_mounts(self):
        """List all active mount points with selection capability"""
        try:
            # Get mounted filesystems using 'mount' command
            result = subprocess.run(
                ['mount'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Create a new window to display mounts
            window = tk.Toplevel(self.root)
            window.title("Active Mount Points")
            window.geometry("1000x500")
            
            # Create a frame for the listbox and scrollbar
            list_frame = ttk.Frame(window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create a listbox to display mounts
            listbox = tk.Listbox(
                list_frame,
                yscrollcommand=scrollbar.set,
                font=('Courier', 10),
                selectmode=tk.SINGLE,
                height=20
            )
            listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            scrollbar.config(command=listbox.yview)
            
            # Parse and add mount points to listbox
            mounts = result.stdout.splitlines()
            if not mounts:
                listbox.insert(tk.END, "No active mount points found.")
                listbox.config(state=tk.DISABLED)
            else:
                for mount in mounts:
                    listbox.insert(tk.END, mount)
            
            # Function to handle selection
            def on_select(event):
                selection = listbox.get(listbox.curselection())
                self.populate_fields_from_mount(selection, window)
            
            # Bind double-click event
            listbox.bind('<Double-1>', on_select)
            
            # Add buttons frame
            btn_frame = ttk.Frame(window)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Add Modify button
            ttk.Button(
                btn_frame,
                text="Modify",
                command=lambda: self.populate_fields_from_mount(
                    listbox.get(listbox.curselection()),
                    window
                ) if listbox.curselection() else None
            ).pack(side=tk.LEFT, padx=5)
            
            # Add close button
            ttk.Button(
                btn_frame,
                text="Close",
                command=window.destroy
            ).pack(side=tk.RIGHT, padx=5)
            
            # Set focus to the window
            window.focus_set()
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to list mount points: {e.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def log(self, message):
        """Add a message to the log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def create_credential_file(self):
        """Create a credential file for CIFS mounts"""
        # Create a new window for credential input
        cred_window = tk.Toplevel(self.root)
        cred_window.title("Create Credential File")
        cred_window.geometry("500x300")
        cred_window.resizable(False, False)
        
        # Center the window
        window_width = 500
        window_height = 300
        screen_width = cred_window.winfo_screenwidth()
        screen_height = cred_window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        cred_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Variables
        cred_name = tk.StringVar()
        username = tk.StringVar()
        password = tk.StringVar()
        domain = tk.StringVar()
        
        # Create form
        ttk.Label(cred_window, text="Credential File Name (without extension):").pack(pady=(10, 0))
        ttk.Entry(cred_window, textvariable=cred_name, width=40).pack(pady=5)
        
        ttk.Label(cred_window, text="Username:").pack(pady=(10, 0))
        ttk.Entry(cred_window, textvariable=username, width=40).pack(pady=5)
        
        ttk.Label(cred_window, text="Password:").pack(pady=(10, 0))
        ttk.Entry(cred_window, textvariable=password, show="*").pack(pady=5)
        
        ttk.Label(cred_window, text="Domain (optional):").pack(pady=(10, 0))
        ttk.Entry(cred_window, textvariable=domain, width=40).pack(pady=5)
        
        # Status label
        status_label = ttk.Label(cred_window, text="", foreground="red")
        status_label.pack(pady=10)
        
        def save_credentials():
            if not cred_name.get() or not username.get() or not password.get():
                status_label.config(text="Error: Name, username and password are required!")
                return
                
            try:
                # Create credentials directory if it doesn't exist
                cred_dir = os.path.expanduser("~/.cifs_credentials")
                os.makedirs(cred_dir, mode=0o700, exist_ok=True)
                
                # Create credential file
                cred_file = os.path.join(cred_dir, f"{cred_name.get()}.cred")
                with open(cred_file, 'w') as f:
                    f.write(f"username={username.get()}\n")
                    f.write(f"password={password.get()}\n")
                    if domain.get():
                        f.write(f"domain={domain.get()}\n")
                
                # Set secure permissions
                os.chmod(cred_file, 0o600)
                
                # Update status
                status_label.config(
                    text=f"Credential file created at:\n{cred_file}\n\n"
                         f"Use it in fstab with:\n"
                         f"credentials={cred_file}",
                    foreground="green"
                )
                
                # Clear password field for security
                password.set("")
                
            except Exception as e:
                status_label.config(text=f"Error creating credential file: {str(e)}")
        
        # Add buttons
        btn_frame = ttk.Frame(cred_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Save", command=save_credentials).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=cred_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Set focus to first field
        cred_window.after(100, lambda: cred_window.focus_force())
        cred_window.grab_set()
    
    def get_sudo_password(self):
        """Display a dialog to enter sudo password"""
        if os.geteuid() == 0:  # Déjà root
            return True
            
        password_window = tk.Toplevel(self.root)
        password_window.title("Authentication Required")
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
        
        ttk.Label(password_window, text="Authentication required to mount the share", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        password_var = tk.StringVar()
        ttk.Label(password_window, text="Sudo password:").pack(pady=5)
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
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Fermeture de la fenêtre avec la touche Entrée
        password_window.bind('<Return>', lambda e: on_ok())
        password_window.bind('<Escape>', lambda e: on_cancel())
        
        # Rendre la fenêtre modale
        password_window.transient(self.root)
        password_window.grab_set()
        self.root.wait_window(password_window)
        
        return result['password'] if result['ok'] else None

    def mount_share(self):
        """Mount the network share"""
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
                self.log("Operation cancelled by user")
                return False
        
        if not all([server, share, mount_point]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        # Vérifier si le point de montage existe
        if not os.path.exists(mount_point):
            # Demander confirmation pour créer le répertoire
            confirm = messagebox.askyesno(
                "Create Directory",
                f"The directory {mount_point} does not exist.\n\nDo you want to create it?",
                icon='question',
                default=messagebox.YES
            )
            
            if not confirm:
                self.log(f"Operation cancelled: mount point {mount_point} does not exist")
                return False
                
            try:
                # Vérifier si le répertoire /mnt existe et est accessible en écriture
                if mount_point.startswith('/mnt/') and not os.access('/mnt', os.W_OK):
                    # Essayer de créer le répertoire avec sudo
                    try:
                        subprocess.run(['sudo', 'mkdir', '-p', mount_point], check=True)
                        subprocess.run(['sudo', 'chown', f'{os.getuid()}:{os.getgid()}', mount_point], check=True)
                        self.log(f"Mount point created with sudo: {mount_point}")
                        messagebox.showinfo("Success", f"Successfully created directory with sudo: {mount_point}")
                    except subprocess.CalledProcessError as e:
                        error_msg = f"Failed to create mount point with sudo: {e}"
                        self.log(error_msg)
                        messagebox.showerror("Error", error_msg + "\n\nYou might need to run this application with sudo or create the directory manually with:\nsudo mkdir -p /mnt/Partages\nsudo chown $USER:$USER /mnt/Partages")
                        return False
                else:
                    # Création normale pour les autres répertoires
                    os.makedirs(mount_point, exist_ok=True)
                    self.log(f"Mount point created: {mount_point}")
                    messagebox.showinfo("Success", f"Successfully created directory: {mount_point}")
            except Exception as e:
                error_msg = f"Failed to create mount point: {e}"
                self.log(error_msg)
                messagebox.showerror("Error", error_msg + "\n\nYou might need to create the directory manually with:\nsudo mkdir -p /mnt/Partages\nsudo chown $USER:$USER /mnt/Partages")
                return False
        
        # Build the mount command
        source = f"//{server}/{share}" if filesystem == "cifs" else f"{server}:{share}"
        mount_cmd = ["sudo", "mount", "-t", filesystem]
        
        # Handle authentication options for CIFS
        if filesystem == "cifs":
            # Create a credentials file for better security with special characters
            creds_file = None
            if username or password or domain:
                try:
                    # Create a secure temporary credentials file
                    import tempfile
                    creds_fd, creds_file = tempfile.mkstemp(prefix='.smbcredentials_')
                    with os.fdopen(creds_fd, 'w') as f:
                        if username:
                            f.write(f'username={username}\n')
                        if password:
                            f.write(f'password={password}\n')
                        if domain:
                            f.write(f'domain={domain}\n')
                    os.chmod(creds_file, 0o600)  # Secure the credentials file
                    
                    # Add credentials file to options
                    creds_options = f"credentials={creds_file}"
                    if options:
                        mount_options = f"{options},{creds_options}"
                    else:
                        mount_options = creds_options
                    mount_cmd.extend(["-o", mount_options])
                except Exception as e:
                    self.log(f"Warning: Could not create credentials file: {e}")
                    # Fallback to command line (less secure)
                    creds = []
                    if username:
                        creds.append(f"username={username}")
                    if password:
                        # Escape special characters in password
                        import shlex
                        creds.append(f"password={shlex.quote(password)}")
                    if domain:
                        creds.append(f"domain={domain}")
                    
                    if creds:
                        creds_str = ",".join(creds)
                        mount_cmd.extend(["-o", f"{options},{creds_str}"] if options else ["-o", creds_str])
                    elif options:
                        mount_cmd.extend(["-o", options])
            else:
                if options:
                    mount_cmd.extend(["-o", options])
        elif options:
            mount_cmd.extend(["-o", options])
        
        mount_cmd.extend([source, mount_point])
        
        # Execute the command
        try:
            # Don't log the full command as it contains sensitive data
            self.log(f"Mounting {source} to {mount_point}...")
            
            # Execute the mount command
            try:
                if os.geteuid() != 0 and sudo_password:
                    # Use Popen to handle the password input
                    try:
                        process = subprocess.Popen(
                            ['sudo', '-S'] + mount_cmd[1:],  # Remove the first 'sudo' and add '-S' to read from stdin
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(input=f"{sudo_password}\n")
                        result = subprocess.CompletedProcess(
                            mount_cmd, 
                            process.returncode,
                            stdout=stdout,
                            stderr=stderr
                        )
                    except Exception as e:
                        self.log(f"Error executing command with sudo: {str(e)}")
                        messagebox.showerror("Error", f"Failed to execute command with sudo: {str(e)}")
                        return False
                else:
                    # Run normally if no password needed
                    result = subprocess.run(
                        mount_cmd,
                        capture_output=True,
                        text=True,
                        errors='replace'  # Handle any encoding issues in output
                    )
            except subprocess.CalledProcessError as e:
                error_msg = f"Command failed with return code {e.returncode}: {e.stderr}"
                self.log(f"Command error: {error_msg}")
                messagebox.showerror("Command Error", error_msg)
                return False
            except Exception as e:
                error_msg = f"Error executing mount command: {str(e)}"
                self.log(f"Execution error: {error_msg}")
                messagebox.showerror("Execution Error", error_msg)
                return False
            finally:
                # Clean up credentials file if it was created
                if 'creds_file' in locals() and creds_file and os.path.exists(creds_file):
                    try:
                        os.unlink(creds_file)
                    except Exception as e:
                        self.log(f"Warning: Could not remove credentials file: {e}")
            
            if result.returncode == 0:
                success_msg = f"Successfully mounted {source} to {mount_point}"
                self.log(success_msg)
                messagebox.showinfo("Success", success_msg)
                return True
            else:
                # Provide more detailed error information
                error_details = []
                if result.stderr:
                    error_details.append(result.stderr.strip())
                if result.stdout:
                    error_details.append(f"Output: {result.stdout.strip()}")
                
                error_msg = f"Failed to mount {source}:\n" + "\n".join(error_details)
                self.log(f"Mount error: {error_msg}")
                messagebox.showerror("Mount Error", error_msg)
                return False
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with return code {e.returncode}: {e.stderr}"
            self.log(f"Command error: {error_msg}")
            messagebox.showerror("Command Error", error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.log(f"Error: {error_msg}")
            messagebox.showerror("Error", error_msg)
            return False
    
    def add_to_fstab(self):
        """Add an entry to the fstab file using a credential file for security"""
        server = self.server.get().strip()
        share = self.share.get().strip()
        mount_point = self.mount_point.get().strip()
        username = self.username.get().strip()
        password = self.password.get()
        domain = self.domain.get().strip()
        filesystem = self.filesystem.get()
        options = self.options.get().strip()
        
        if not all([server, share, mount_point]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return False
        
        # Build source path
        source = f"//{server}/{share}" if filesystem == "cifs" else f"{server}:{share}"
        
        # Prepare fstab options
        fstab_options = options
        creds_file_path = None
        
        if filesystem == "cifs" and (username or password or domain):
            try:
                # Create credentials directory if it doesn't exist
                cred_dir = os.path.expanduser("~/.cifs_credentials")
                os.makedirs(cred_dir, mode=0o700, exist_ok=True)
                
                # Create a unique credential filename based on server and share
                cred_name = f"{server}_{share.replace('/', '_')}.cred"
                creds_file_path = os.path.join(cred_dir, cred_name)
                
                # Create the credentials file
                with open(creds_file_path, 'w') as f:
                    if username:
                        f.write(f"username={username}\n")
                    if password:
                        f.write(f"password={password}\n")
                    if domain:
                        f.write(f"domain={domain}\n")
                
                # Set secure permissions
                os.chmod(creds_file_path, 0o600)
                
                # Add credentials file to options
                creds_option = f"credentials={creds_file_path}"
                fstab_options = f"{options},{creds_option}" if options else creds_option
                
                self.log(f"Created credentials file: {creds_file_path}")
                
            except Exception as e:
                error_msg = f"Failed to create credentials file: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("Error", error_msg)
                return False
        
        # Build the fstab line
        fstab_line = f"{source}\t{mount_point}\t{filesystem}\t{fstab_options}\t0 0\n"
        
        try:
            # Sauvegarder l'ancien fstab
            with open("/etc/fstab", "r") as f:
                fstab_content = f.read()
            
            # Check if entry already exists
            lines = fstab_content.splitlines()
            entry_exists = False
            new_lines = []
            
            for line in lines:
                # Skip comments and empty lines
                if line.strip().startswith('#') or not line.strip():
                    new_lines.append(line)
                    continue
                
                # Check if this is the mount point we're looking for
                parts = line.split()
                if len(parts) >= 2 and parts[1] == mount_point:
                    # Ask user if they want to update the existing entry
                    if messagebox.askyesno(
                        "Entry Exists",
                        f"An entry for {mount_point} already exists in fstab.\n\n"
                        f"Current: {line}\n"
                        f"New:     {fstab_line.strip()}\n\n"
                        "Do you want to update it?"
                    ):
                        new_lines.append(fstab_line.strip())
                        entry_exists = True
                        self.log(f"Updated fstab entry for {mount_point}")
                    else:
                        new_lines.append(line)  # Keep the existing entry
                        self.log("Keeping existing fstab entry")
                        return False
                else:
                    new_lines.append(line)
            
            # If we didn't find an existing entry, add the new one
            if not entry_exists:
                new_lines.append(fstab_line.strip())
                self.log(f"Added new entry to /etc/fstab:")
            
            # Write the updated fstab file
            with open("/etc/fstab", "w") as f:
                f.write("\n".join(new_lines) + "\n")
            
            self.log(fstab_line.strip())
            messagebox.showinfo("Success", "The fstab file has been updated")
            return True
            
        except PermissionError:
            # Try with sudo
            try:
                # Read current fstab with sudo
                read_cmd = ["sudo", "cat", "/etc/fstab"]
                result = subprocess.run(read_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = f"Error reading fstab: {result.stderr}"
                    self.log(error_msg)
                    messagebox.showerror("Error", error_msg)
                    return False
                
                # Process the fstab content
                lines = result.stdout.splitlines()
                entry_exists = False
                new_lines = []
                
                for line in lines:
                    # Skip comments and empty lines
                    if line.strip().startswith('#') or not line.strip():
                        new_lines.append(line)
                        continue
                    
                    # Check if this is the mount point we're looking for
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        # Ask user if they want to update the existing entry
                        if messagebox.askyesno(
                            "Entry Exists",
                            f"An entry for {mount_point} already exists in fstab.\n\n"
                            f"Current: {line}\n"
                            f"New:     {fstab_line.strip()}\n\n"
                            "Do you want to update it?"
                        ):
                            new_lines.append(fstab_line.strip())
                            entry_exists = True
                            self.log(f"Updated fstab entry for {mount_point}")
                        else:
                            new_lines.append(line)  # Keep the existing entry
                            self.log("Keeping existing fstab entry")
                            return False
                    else:
                        new_lines.append(line)
                
                # If we didn't find an existing entry, add the new one
                if not entry_exists:
                    new_lines.append(fstab_line.strip())
                    self.log(f"Added new entry to /etc/fstab:")
                
                # Create a temporary file with the new content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_f:
                    temp_f.write("\n".join(new_lines) + "\n")
                    temp_path = temp_f.name
                
                try:
                    # Replace fstab with the new content using sudo
                    cmd = ["sudo", "cp", temp_path, "/etc/fstab"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.log(fstab_line.strip())
                        messagebox.showinfo("Success", "The fstab file has been updated")
                        return True
                    else:
                        error_msg = f"Error updating fstab: {result.stderr}"
                        self.log(error_msg)
                        messagebox.showerror("Error", error_msg)
                        return False
                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        self.log(f"Warning: Could not remove temporary file: {e}")
                
            except Exception as e:
                error_msg = f"Error adding to fstab: {e}"
                self.log(error_msg)
                messagebox.showerror("Error", error_msg)
                return False
    
    def do_all(self):
        """Perform all operations: mount and add to fstab"""
        if self.mount_share():
            self.add_to_fstab()

def main():
    root = tk.Tk()
    app = NetworkMounter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
