# ConnectDrive

A Python-based network drive mounter with a graphical interface for managing network shares on Linux systems.

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

## Building a Standalone Executable

You can create a standalone executable that doesn't require Python to be installed.

### Prerequisites

```bash
sudo apt-get install python3-venv python3-pip
```

### Build Steps

1. Clone the repository (if you haven't already):
   ```bash
   git clone https://github.com/bermotard/connectdrive.git
   cd connectdrive
   ```

2. Make the build script executable and run it:
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

3. The executable will be created in the `dist` directory.

### Running the Executable

```bash
# Navigate to the dist directory
cd dist

# Make the file executable (if needed)
chmod +x NetworkMounter

# Run the application
./NetworkMounter
```

### Distribution

To share the application, simply copy the `NetworkMounter` file from the `dist` directory. The recipient needs to:

1. Have the required system packages installed:
   ```bash
   sudo apt-get install cifs-utils nfs-common
   ```

2. Make the file executable:
   ```bash
   chmod +x NetworkMounter
   ```

3. Run it:
   ```bash
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
