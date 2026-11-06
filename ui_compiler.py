# ui_compiler.py
import os
import sys
from PyQt6.uic import compileUi

UI_FILE = "Yt Downloader.ui"
PY_FILE = "DownloaderForm.py"

def ensure_ui_compiled():
#Purpose : This function check if the *.ui file (QT Designer file) has changed
# if it has changed it will create a Python code version in file PY_FILE.

    # In a PyInstaller build the form is already compiled into the exe
    if getattr(sys, 'frozen', False):
        return

    # If the .py file doesn't exist, or if the .ui file was modified more recently:
    if not os.path.exists(PY_FILE) or os.path.getmtime(UI_FILE) > os.path.getmtime(PY_FILE):
        print(f"[*] Detected changes in {UI_FILE}. Recompiling to {PY_FILE}...")
        with open(PY_FILE, "w", encoding="utf-8") as output_file:  
            compileUi(UI_FILE, output_file)