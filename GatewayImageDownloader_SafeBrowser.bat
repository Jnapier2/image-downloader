@echo off
rem Asset ID: IMGDL-ENTRYPOINT-SAFE-BROWSER
rem Version: 2026.08.09.1
rem Build: v2179-readonly-gate-order-repair
rem Status: current
rem Sensitivity: public-source
rem Copyright © 2026 Gateway Information Group LLC. All rights reserved.
setlocal EnableExtensions
title Gateway Image Downloader Safe Browser
echo =========================================
echo Gateway Image Downloader Safe Browser
echo =========================================
echo Using bot folder: %~dp0
echo.
set "GID_LAUNCH_MODE=safe_browser"
set "GID_SHIM_BANNER_SHOWN=1"
call "%~dp0GatewayImageDownloader.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
