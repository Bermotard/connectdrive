#!/bin/bash

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  The venv directory does not exist. Creating a new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
fi

# Install dependencies
pip install -r requirements.txt

# Install PyInstaller if needed
pip install pyinstaller

# Clean previous builds
rm -rf build dist

# Create output directory if it doesn't exist
mkdir -p dist

# Create the executable with the project structure
pyinstaller \
  --name NetworkMounter \
  --onefile \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "version.txt:." \
  --add-data "src/config:config" \
  --add-data "src/gui:gui" \
  --add-data "src/services:services" \
  --add-data "src/utils:utils" \
  --hidden-import "PyQt5.QtWidgets" \
  --hidden-import "PyQt5.QtCore" \
  --hidden-import "PyQt5.QtGui" \
  --hidden-import "cryptography" \
  --hidden-import "keyring" \
  --add-binary "/lib/x86_64-linux-gnu/libc.so.6:." \
  --add-binary "/lib/x86_64-linux-gnu/libm.so.6:." \
  src/__main__.py

# Check if compilation was successful
if [ $? -eq 0 ]; then
    # Make the executable... executable
    chmod +x dist/NetworkMounter
    echo "✅ Build completed successfully! The executable is in the 'dist/' directory"
    echo "   You can run it with: ./dist/NetworkMounter"
else
    echo "❌ Error during compilation. Check the error messages above."
    exit 1
fi
