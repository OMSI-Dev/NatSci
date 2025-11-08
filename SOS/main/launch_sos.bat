@echo off
REM Launcher for SOS with PyQt5 GUI Overlay
REM Uses LibreOffice's Python with PyQt5

echo SOS LibreOffice Controller with GUI Overlay (PyQt5)
echo ===================================================
echo.

REM Check if PyQt5 is installed
"C:\Program Files\LibreOffice\program\python.exe" -c "import PyQt5" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo PyQt5 not found. Installing...
    echo.
    "C:\Program Files\LibreOffice\program\python.exe" -m pip install PyQt5
    echo.
    echo ✓ PyQt5 installation complete
    echo.
) else (
    echo ✓ PyQt5 already installed
    echo.
)

echo Starting SOS Controller...
echo.

"C:\Program Files\LibreOffice\program\python.exe" sdc.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Script failed with error code %ERRORLEVEL%
    pause
)
