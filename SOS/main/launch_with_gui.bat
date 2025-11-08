@echo off
REM Launcher for SOS with GUI Overlay
REM Uses system Python 3.11 with LibreOffice UNO bridge

echo SOS LibreOffice Controller with GUI Overlay
echo ============================================
echo.

REM Set LibreOffice Python path
set PYTHONPATH=C:\Program Files\LibreOffice\program;%PYTHONPATH%

REM Try to find Python 3.11
set PYTHON_CMD=

REM Check for Python 3.11 in user's AppData (where we found it)
if exist "C:\Users\OMSI-Admin\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=C:\Users\OMSI-Admin\AppData\Local\Programs\Python\Python311\python.exe
    echo Found Python 3.11 in AppData
    goto :run
)

REM Fallback: Check other common locations
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    echo Found Python 3.11 at C:\Python311
    goto :run
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    echo Found Python 3.11 in AppData
    goto :run
)

REM Check if python in PATH is 3.11
python --version 2>nul | findstr "3.11" >nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    echo Found Python 3.11 in PATH
    goto :run
)

REM Python 3.11 not found
echo ERROR: Python 3.11 not found!
echo.
echo Please install Python 3.11 from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:run
echo Using Python: %PYTHON_CMD%
echo PYTHONPATH: %PYTHONPATH%
echo.
echo Starting SOS Controller...
echo.

"%PYTHON_CMD%" sdc.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Script failed with error code %ERRORLEVEL%
    pause
)
