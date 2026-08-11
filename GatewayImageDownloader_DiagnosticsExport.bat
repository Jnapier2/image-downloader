@echo off
rem Asset ID: IMGDL-ENTRYPOINT-DIAGNOSTICS-EXPORT
rem Version: 2026.08.09.1
rem Build: v2176-canonical-entrypoint-project-local-outputs
rem Status: current
rem Sensitivity: public-source
rem Copyright © 2026 Gateway Information Group LLC. All rights reserved.
setlocal EnableExtensions
title Gateway Image Downloader Diagnostics and Export
echo =========================================
echo Gateway Image Downloader Diagnostics and Export
echo =========================================
echo Using bot folder: %~dp0
echo.
set "GID_LAUNCH_MODE=diagnostics_export"
set "GID_SHIM_BANNER_SHOWN=1"
call "%~dp0GatewayImageDownloader.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
