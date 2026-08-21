#!/usr/bin/env python3
"""
Script pour générer ou mettre à jour le fichier build.sh
"""

def generate_build_sh():
    """Génère le contenu du fichier build.sh"""
    content = '''#!/bin/bash

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
fi

# Install required packages
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
rm -rf build dist

# Create the executable
# (Tkinter is detected automatically by PyInstaller; no hidden imports needed)
pyinstaller \\
  --name NetworkMounter \\
  --onefile \\
  --windowed \\
  --clean \\
  --noconfirm \\
  src/__main__.py

# Make the executable executable
chmod +x dist/NetworkMounter

echo "Build complete! The executable is in the 'dist' directory."
'''
    return content

def main():
    """Main function"""
    try:
        with open('build.sh', 'w', encoding='utf-8') as f:
            f.write(generate_build_sh())
        print("✅ build.sh file generated successfully!")
    except Exception as e:
        print(f"❌ Error generating file: {e}")

if __name__ == "__main__":
    main()
