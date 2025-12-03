"""
Build executable for Officials Tracker
Requires: pip install pyinstaller
"""
import PyInstaller.__main__
import sys
import os

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# PyInstaller arguments
args = [
    'app.py',  # Main script
    '--name=OfficialTracker',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # No console window (GUI mode)
    '--icon=NONE',  # No icon (can add later)
    f'--add-data={os.path.join(project_root, "src")};src',  # Include src directory
    f'--add-data={os.path.join(project_root, "config.py")};.',  # Include config
    '--hidden-import=streamlit',
    '--hidden-import=pandas',
    '--hidden-import=openpyxl',
    '--hidden-import=filelock',
    '--hidden-import=streamlit.runtime.scriptrunner.magic_funcs',
    '--hidden-import=streamlit.web.cli',
    '--collect-all=streamlit',
    '--noconfirm',  # Overwrite without asking
]

print("🔨 Building executable...")
print(f"Project root: {project_root}")
print(f"Script dir: {script_dir}")
print()

# Run PyInstaller
PyInstaller.__main__.run(args)

print()
print("✅ Build complete!")
print(f"Executable location: {os.path.join(project_root, 'dist', 'OfficialTracker.exe')}")
