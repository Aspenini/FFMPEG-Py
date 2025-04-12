@echo off
setlocal

echo [FreqShift Build Script]

REM === Step 1: Setup virtual environment ===
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM === Step 2: Install dependencies ===
echo Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt

REM === Step 3: Build FreqShift executable ===
echo Building with PyInstaller...
pyinstaller --onefile --windowed --icon=img/wave.ico FreqShift.py

echo Done! Output is in the /dist folder.
pause
