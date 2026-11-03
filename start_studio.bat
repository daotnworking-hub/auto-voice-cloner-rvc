@echo off
chcp 65001 >nul
title AutoVoiceStudio - RTX 4060 Dashboard

cd /d "%~dp0"

echo ==============================================================================
echo       KHOI DONG AUTO VOICE STUDIO - RTX 4060 WEB DASHBOARD
echo ==============================================================================
echo.

set "PYTHON_EXE=env\Scripts\python.exe"
if exist "..\Applio-RVC\env\Scripts\python.exe" (
    set "PYTHON_EXE=..\Applio-RVC\env\Scripts\python.exe"
)

if not exist "%PYTHON_EXE%" (
    echo [LOI] Chua tim thay moi truong Python! Hay chay 'setup_home_pc.bat' truoc!
    pause
    exit /b 1
)

echo Dang khoi dong Web Server tai http://127.0.0.1:7865 ...
start "" http://127.0.0.1:7865
%PYTHON_EXE% auto_studio.py
pause
