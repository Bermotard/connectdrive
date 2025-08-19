# ConnectDrive

A Python project for managing network connections and storage operations.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/bermotard/connectdrive.git
cd connectdrive
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
# .\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Network Drive Mounter

The `network_mounter.py` program provides a graphical interface to mount network shares and add them to the fstab file.

#### Prerequisites

- Python 3.6 or higher
- Required system packages (for Ubuntu/Debian):
  ```bash
  sudo apt-get install cifs-utils nfs-common
  ```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Launch the Program

```bash
python network_mounter.py
```

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

## Project Structure

```
connectdrive/
├── src/           # Source code
├── tests/         # Unit tests
├── docs/          # Documentation
├── .gitignore
├── README.md
└── requirements.txt
```
