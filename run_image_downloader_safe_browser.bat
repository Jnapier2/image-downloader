@echo off
rem Asset ID: IMGDL-LAUNCHER-BROWSER
rem Version: 2026.08.08.1
rem Build: v2175-queue-autosave-recovery-3worker-session-list
rem Status: current
rem Sensitivity: public-source
rem Tags: image-downloader,launcher,safe-browser,playwright,windows,portable,asset-metadata
rem Copyright © 2026 Gateway Information Group LLC. All rights reserved.
setlocal EnableExtensions

set "SCRIPT_NAME=image_downloader.py"
set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR_NOSLASH=%%~fI"
set "BOT_DIR=%SOURCE_DIR_NOSLASH%"
set "BOT_DIR_SOURCE=project folder"
set "ENV_BOT_DIR=%IMAGE_DOWNLOADER_BOT_DIR%"
set "EXIT_CODE=0"

if defined ENV_BOT_DIR call :consider_override
title Gateway Image Downloader Safe Browser
echo =========================================
echo Gateway Image Downloader Safe Browser
echo =========================================
echo Using bot folder: %BOT_DIR%
echo Version: 2026.08.08.1
echo Build: v2175-queue-autosave-recovery-3worker-session-list
echo.
echo Started: %DATE% %TIME%
echo Target source: %BOT_DIR_SOURCE%
echo Launch mode: optional trusted-sites-only browser capture; portable project-folder first.
echo.

if not exist "%BOT_DIR%\%SCRIPT_NAME%" (
    echo Missing %SCRIPT_NAME%.
    echo Extract the complete ZIP and run this BAT from the extracted project folder.
    echo.
    set "EXIT_CODE=1"
    goto :end
)
call :verify_write_dir "%BOT_DIR%"
if errorlevel 1 (
    echo The bot folder is not writable: %BOT_DIR%
    echo Move or extract the package to a normal writable folder and try again.
    echo.
    set "EXIT_CODE=1"
    goto :end
)
cd /d "%BOT_DIR%"
if errorlevel 1 (
    echo Could not enter bot folder: %BOT_DIR%
    echo.
    set "EXIT_CODE=1"
    goto :end
)
call :find_python
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :end
)
call :verify_release_integrity
if errorlevel 1 (
    set "EXIT_CODE=23"
    goto :end
)
call :ensure_core_dependencies
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :end
)
call :ensure_browser_dependencies
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :end
)

echo Safety notice:
echo - Use Safe Browser Mode only for sites you trust
echo - Downloaded files are validated as images and are never executed
echo - Standard Mode remains the preferred daily launcher
echo - Computer auto-labeling is diagnostic-only and never blocks launch or changes paths/features
echo.
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --browser-mode %*
set "EXIT_CODE=%ERRORLEVEL%"
goto :end

:consider_override
set "ENV_BOT_DIR=%ENV_BOT_DIR:"=%"
for %%I in ("%ENV_BOT_DIR%") do set "ENV_BOT_DIR=%%~fI"
if exist "%ENV_BOT_DIR%\%SCRIPT_NAME%" if exist "%ENV_BOT_DIR%\VERSION.txt" if exist "%ENV_BOT_DIR%\MANIFEST.json" if exist "%ENV_BOT_DIR%\PACKAGE_METADATA.json" (
    set "BOT_DIR=%ENV_BOT_DIR%"
    set "BOT_DIR_SOURCE=IMAGE_DOWNLOADER_BOT_DIR override (complete release controls present)"
) else (
    echo Notice: IMAGE_DOWNLOADER_BOT_DIR is incomplete or missing required release controls.
    echo Required: %SCRIPT_NAME%, VERSION.txt, MANIFEST.json, PACKAGE_METADATA.json.
    echo Using the project folder instead.
    echo.
)
goto :eof

:verify_write_dir
set "TEST_FILE=%~1\.launcher_write_test_%RANDOM%.tmp"
> "%TEST_FILE%" echo ok
if errorlevel 1 exit /b 1
del "%TEST_FILE%" >nul 2>nul
exit /b 0

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=py -3"
        goto :eof
    )
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
        goto :eof
    )
)
echo Python 3.9 or newer was not found or could not run.
echo Install current 64-bit Python from python.org and enable Add Python to PATH.
echo.
exit /b 1

:verify_release_integrity
echo Verifying v2.17.5 release identity and managed-file hashes...
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --verify-release
if errorlevel 1 (
    echo.
    echo ERROR: Release identity/integrity verification BLOCKED startup.
    echo No dependency install, browser start, or download activity will continue.
    echo Run run_diagnose_export.bat for Support Export20 evidence, or restore the complete verified release ZIP.
    echo.
    exit /b 23
)
echo Release identity gate: PASS
echo.
goto :eof

:ensure_core_dependencies
%PY_CMD% -c "import requests, bs4, PIL" >nul 2>nul
if not errorlevel 1 goto :eof
echo Installing bounded core packages: requests beautifulsoup4 pillow
%PY_CMD% -m pip install --disable-pip-version-check "requests>=2.32,<3" "beautifulsoup4>=4.12,<5" "pillow>=10,<13"
if errorlevel 1 (
    echo Retrying as a user-level Python install...
    %PY_CMD% -m pip install --user --disable-pip-version-check "requests>=2.32,<3" "beautifulsoup4>=4.12,<5" "pillow>=10,<13"
)
%PY_CMD% -c "import requests, bs4, PIL" >nul 2>nul
if errorlevel 1 (
    echo.
    echo Failed to verify one or more core packages.
    echo.
    exit /b 1
)
goto :eof

:ensure_browser_dependencies
%PY_CMD% -c "import playwright" >nul 2>nul
if errorlevel 1 (
    echo Installing bounded Playwright package for optional Safe Browser Mode...
    %PY_CMD% -m pip install --disable-pip-version-check "playwright>=1.45,<2"
    if errorlevel 1 (
        echo Retrying as a user-level Python install...
        %PY_CMD% -m pip install --user --disable-pip-version-check "playwright>=1.45,<2"
    )
    %PY_CMD% -c "import playwright" >nul 2>nul
    if errorlevel 1 (
        echo.
        echo Failed to verify the Playwright package.
        echo.
        exit /b 1
    )
)
echo Ensuring Chromium browser runtime is installed for optional Safe Browser Mode...
%PY_CMD% -m playwright install chromium
if errorlevel 1 (
    echo.
    echo Failed to install the Chromium runtime for Playwright.
    echo Standard Mode still works through run_image_downloader.bat.
    echo.
    exit /b 1
)
goto :eof

:end
echo.
if "%EXIT_CODE%"=="0" (
    echo Gateway Image Downloader Safe Browser finished successfully.
) else (
    echo Gateway Image Downloader Safe Browser finished with exit code %EXIT_CODE%.
)
echo Finished: %DATE% %TIME%
echo.
pause
endlocal & exit /b %EXIT_CODE%
