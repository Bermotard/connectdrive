# ConnectDrive

Network share mounting tool with a graphical interface for Linux.

## Features

- Mount/unmount network shares (CIFS/NFS)
- Mount point management
- Mount options configuration
- Secure credential management
- Integration with fstab for permanent mounts
- Intuitive graphical interface

## Prerequisites

- Python 3.8 or higher
- System packages:
  - `cifs-utils` for CIFS/Samba support
  - `nfs-common` for NFS support
  - `python3-tk` for the graphical interface

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bermotard/connectdrive.git
   cd connectdrive
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # OR
   # .\venv\Scripts\activate  # On Windows
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Development mode

```bash
python3 -m src
```

### System installation

```bash
# Install in development mode
pip install -e .

# Launch the application
connectdrive
```

### Building an executable

```bash
# Install pyinstaller
pip install pyinstaller

# Build the executable
./build.sh

# Run the application
./dist/NetworkMounter
```

## Project Structure

```
connectdrive/
├── src/                    # Source code
│   ├── config/            # Configuration
│   ├── gui/               # Graphical interface
│   │   ├── dialogs/       # Dialog boxes
│   │   └── widgets/       # Custom widgets
│   ├── services/          # Business services
│   └── utils/             # Utilities
├── tests/                 # Unit tests
├── docs/                  # Documentation
├── resources/             # Resources (icons, etc.)
├── .gitignore
├── MANIFEST.in
├── README.md
├── requirements.txt
└── setup.py
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## Author

[Your Name] - [your.email@example.com]

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
   ./NetworkMounter
   ```

## Development

#### Features

1. **Mount Network Share**: Mounts a network share immediately
2. **Add to fstab**: Adds an entry to /etc/fstab for automatic mounting at boot
3. **Do Everything**: Mounts the share and adds it to fstab in one operation

#### Parameters

- **Server**: IP address or hostname of the server
- **Share**: Name of the network share
- **Mount Point**: Local directory where the share will be mounted
- **Username**: Username for authentication
- **Password**: Password for authentication
- **Domain**: (Optional) Domain for authentication
- **Filesystem Type**: CIFS (Samba) or NFS
- **Options**: Additional mount options (comma-separated)

#### Usage Example

1. Enter the server connection details
2. Click "Mount" to mount the share immediately
3. If successful, click "Add to fstab" to make it permanent
4. Or use "Do Everything" to perform both operations at once
