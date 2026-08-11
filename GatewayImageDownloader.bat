@echo off
rem Asset ID: IMGDL-ENTRYPOINT-CANONICAL
rem Version: 2026.08.09.1
rem Build: v2176-canonical-entrypoint-project-local-outputs
rem Status: current
rem Sensitivity: public-source
rem Tags: image-downloader,canonical-entrypoint,windows,portable
rem Copyright © 2026 Gateway Information Group LLC. All rights reserved.
setlocal EnableExtensions

set "SCRIPT_NAME=image_downloader.py"
set "BOT_DIR=%~dp0"
for %%I in ("%BOT_DIR%.") do set "BOT_DIR=%%~fI"
set "MODE=%GID_LAUNCH_MODE%"
if not defined MODE set "MODE=standard"
set "EXIT_CODE=0"
set "PY_CMD="

if /I "%MODE%"=="safe_browser" (
    title Gateway Image Downloader Safe Browser
    set "MODE_LABEL=Safe Browser"
) else if /I "%MODE%"=="diagnostics_export" (
    title Gateway Image Downloader Diagnostics and Export
    set "MODE_LABEL=Diagnostics and Export"
) else (
    title Gateway Image Downloader
    set "MODE=standard"
    set "MODE_LABEL=Standard"
)

if not defined GID_SHIM_BANNER_SHOWN (
    echo =========================================
    echo Gateway Image Downloader
    echo =========================================
    echo Using bot folder: %BOT_DIR%
    echo.
)
echo Execution namespace: GatewayImageDownloader
echo Canonical entrypoint: GatewayImageDownloader.bat
echo Version: 2026.08.09.1
echo Build: v2176-canonical-entrypoint-project-local-outputs
echo Mode: %MODE_LABEL%
echo Started: %DATE% %TIME%
if defined GID_LEGACY_ALIAS echo Legacy alias redirect: %GID_LEGACY_ALIAS%
echo Project-local outputs: downloads, logs, state, temp, reports, exports
if defined IMAGE_DOWNLOADER_BOT_DIR (
    echo Notice: IMAGE_DOWNLOADER_BOT_DIR is no longer used to redirect the runtime root.
    echo Launch GatewayImageDownloader.bat from the complete extracted project folder instead.
)
echo.

if not exist "%BOT_DIR%\%SCRIPT_NAME%" (
    echo ERROR: Missing %SCRIPT_NAME% next to the canonical launcher.
    echo Recovery: extract the complete release ZIP and run GatewayImageDownloader.bat from that folder.
    set "EXIT_CODE=1"
    goto :end
)
if not exist "%BOT_DIR%\VERSION.txt" (
    echo ERROR: Missing VERSION.txt.
    set "EXIT_CODE=1"
    goto :end
)
if not exist "%BOT_DIR%\MANIFEST.json" (
    echo ERROR: Missing MANIFEST.json.
    set "EXIT_CODE=1"
    goto :end
)
if not exist "%BOT_DIR%\PACKAGE_METADATA.json" (
    echo ERROR: Missing PACKAGE_METADATA.json.
    set "EXIT_CODE=1"
    goto :end
)

call :verify_write_dir "%BOT_DIR%"
if errorlevel 1 (
    echo ERROR: Project folder is not writable: %BOT_DIR%
    echo Recovery: move or extract the package to a normal writable folder and try again.
    set "EXIT_CODE=1"
    goto :end
)

cd /d "%BOT_DIR%"
if errorlevel 1 (
    echo ERROR: Could not enter project folder: %BOT_DIR%
    set "EXIT_CODE=1"
    goto :end
)

call :find_python
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :end
)

if /I "%MODE%"=="diagnostics_export" goto :diagnostics_export

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

if /I "%MODE%"=="safe_browser" (
    call :ensure_browser_dependencies
    if errorlevel 1 (
        set "EXIT_CODE=1"
        goto :end
    )
    echo Ready: release identity PASS; starting trusted-sites-only Safe Browser Mode.
    echo.
    %PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --browser-mode %*
) else (
    echo Ready: release identity PASS; starting Standard Mode.
    echo Queue: up to 100 saved URLs; maximum 3 active image downloads.
    echo Session list: reports\LATEST_DOWNLOAD_LIST.txt plus timestamped retained copies.
    echo Support export: exports\IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip
    echo.
    %PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --standard %*
)
set "EXIT_CODE=%ERRORLEVEL%"
goto :end

:diagnostics_export
echo Checking release identity for diagnostic evidence...
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --verify-release
if errorlevel 1 (
    echo Release identity gate is BLOCKED. Report-only Export20 remains intentionally available.
    echo.
)
echo Ready: creating report-only project-local Support Export20.
echo.
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --export-support %*
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="0" (
    echo.
    echo Support export created:
    echo %BOT_DIR%\exports\IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip
)
goto :end

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
        exit /b 0
    )
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
        exit /b 0
    )
)
echo ERROR: Python 3.9 or newer was not found or could not run.
echo Install current 64-bit Python from python.org and enable Add Python to PATH.
exit /b 1

:verify_release_integrity
echo Verifying release identity and package-managed SHA-256 hashes...
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --verify-release
if errorlevel 1 (
    echo.
    echo ERROR: Release identity/integrity verification BLOCKED startup.
    echo No dependency install, browser start, or download/network activity will continue.
    echo Run GatewayImageDownloader_DiagnosticsExport.bat for Support Export20 evidence.
    echo Recovery: restore the complete verified release ZIP; verification never rewrites managed files.
    echo.
    exit /b 23
)
echo Release identity gate: PASS
echo.
exit /b 0

:ensure_core_dependencies
%PY_CMD% -c "import requests, bs4, PIL" >nul 2>nul
if not errorlevel 1 exit /b 0
echo Installing bounded core packages: requests beautifulsoup4 pillow
echo This uses normal Python packaging and does not disable Norton, SmartScreen, or Windows protections.
%PY_CMD% -m pip install --disable-pip-version-check "requests>=2.32,<3" "beautifulsoup4>=4.12,<5" "pillow>=10,<13"
if errorlevel 1 (
    echo Retrying as a user-level Python install...
    %PY_CMD% -m pip install --user --disable-pip-version-check "requests>=2.32,<3" "beautifulsoup4>=4.12,<5" "pillow>=10,<13"
)
%PY_CMD% -c "import requests, bs4, PIL" >nul 2>nul
if errorlevel 1 (
    echo ERROR: Failed to verify one or more core Python packages.
    exit /b 1
)
exit /b 0

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
        echo ERROR: Failed to verify the Playwright package.
        exit /b 1
    )
)
echo Ensuring Chromium browser runtime is installed for optional Safe Browser Mode...
%PY_CMD% -m playwright install chromium
if errorlevel 1 (
    echo ERROR: Failed to install the Chromium runtime for Playwright.
    echo Standard Mode remains available through GatewayImageDownloader.bat.
    exit /b 1
)
exit /b 0

:end
echo.
if "%EXIT_CODE%"=="0" (
    echo Ready: Gateway Image Downloader session completed successfully.
) else (
    echo ERROR: Gateway Image Downloader finished with exit code %EXIT_CODE%.
)
echo Finished: %DATE% %TIME%
echo.
if not "%EXIT_CODE%"=="0" pause
endlocal & exit /b %EXIT_CODE%
