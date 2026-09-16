@echo off
chcp 65001 >nul
title HarmonyOS Full Docs Update
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0one-click-update.ps1" -Mode All
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo Update failed. Review the error above and scraper\data\logs.
pause
exit /b %RESULT%
