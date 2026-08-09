@echo off
rem Asset ID: IMGDL-LAUNCHER-EXPORT
rem Version: 2026.08.08.1
rem Build: v2175-queue-autosave-recovery-3worker-session-list
rem Status: current
rem Sensitivity: public-source
rem Tags: image-downloader,launcher,diagnostics,export20,windows,portable,asset-metadata
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
title Gateway Image Downloader Diagnostics and Export
echo =========================================
echo Gateway Image Downloader Diagnostics and Export
echo =========================================
echo Using bot folder: %BOT_DIR%
echo Version: 2026.08.08.1
echo Build: v2175-queue-autosave-recovery-3worker-session-list
echo.
echo Started: %DATE% %TIME%
echo Target source: %BOT_DIR_SOURCE%
echo Report-only export: no dependency install, config migration, cleanup sync, or download activity.
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
echo Checking release identity for diagnostic evidence...
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --verify-release
if errorlevel 1 (
    echo Release identity gate is BLOCKED. Diagnostic/Export20 is intentionally still allowed.
    echo.
)
echo Creating one redacted support ZIP...
echo.
%PY_CMD% "%BOT_DIR%\%SCRIPT_NAME%" --export-support %*
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="0" (
    echo.
    echo Support bundle created:
    echo %BOT_DIR%\IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip
)
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

:end
echo.
if "%EXIT_CODE%"=="0" (
    echo Gateway Image Downloader export finished successfully.
) else (
    echo Gateway Image Downloader export finished with exit code %EXIT_CODE%.
)
echo Finished: %DATE% %TIME%
echo.
pause
endlocal & exit /b %EXIT_CODE%
