@echo off
rem Builds dist\SmartCorrect\SmartCorrect.exe with PyInstaller.
rem Then open installer\smartcorrect.iss in Inno Setup to make the installer.
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --windowed --name SmartCorrect run_smartcorrect.py
