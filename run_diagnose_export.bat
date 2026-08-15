@echo off
rem Asset ID: IMGDL-LEGACY-ALIAS-DIAGNOSTICS
rem Version: 2026.08.09.1
rem Build: v2179-readonly-gate-order-repair
rem Status: compatibility-redirect
rem Copyright © 2026 Gateway Information Group LLC. All rights reserved.
setlocal EnableExtensions
title Gateway Image Downloader Diagnostics Legacy Redirect
echo =========================================
echo Gateway Image Downloader Diagnostics Legacy Redirect
echo =========================================
echo Using bot folder: %~dp0
echo Redirecting run_diagnose_export.bat to GatewayImageDownloader_DiagnosticsExport.bat
echo.
set "GID_LAUNCH_MODE=diagnostics_export"
set "GID_SHIM_BANNER_SHOWN=1"
set "GID_LEGACY_ALIAS=run_diagnose_export.bat"
call "%~dp0GatewayImageDownloader.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
