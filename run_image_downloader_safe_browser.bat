@echo off
setlocal
cd /d "%~dp0" || exit /b 1

set "PYTHON_EXE="
set "PYTHON_ARGS="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE where py >nul 2>nul && set "PYTHON_EXE=py" && set "PYTHON_ARGS=-3"
if not defined PYTHON_EXE where python >nul 2>nul && set "PYTHON_EXE=python"

if not defined PYTHON_EXE (
    echo Python 3.11 or newer was not found.
    echo See README.md for setup instructions.
    exit /b 1
)

"%PYTHON_EXE%" %PYTHON_ARGS% -c "import sys; raise SystemExit(0 if sys.version_info ^>= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Python 3.11 or newer is required.
    exit /b 1
)

"%PYTHON_EXE%" %PYTHON_ARGS% -c "import requests, bs4, PIL, playwright" >nul 2>nul
if errorlevel 1 (
    echo Optional browser-mode dependencies are missing.
    echo Run: "%PYTHON_EXE%" %PYTHON_ARGS% -m pip install -r requirements-browser.txt
    echo Then: "%PYTHON_EXE%" %PYTHON_ARGS% -m playwright install chromium
    exit /b 1
)

echo Use browser mode only on trusted sites where downloading is permitted.
"%PYTHON_EXE%" %PYTHON_ARGS% image_downloader.py --browser-mode %*
exit /b %ERRORLEVEL%
