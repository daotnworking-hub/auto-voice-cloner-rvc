@echo off
chcp 65001 >nul
title AutoVoiceStudio - Cai Dat Tu Dong Cho May Nha (RTX 4060)

echo ==============================================================================
echo       AUTO VOICE STUDIO - HE THONG CLONE VOICE TU DONG CHO RTX 4060
echo       Cau hinh toi uu: Intel Core i5-14400F ^| 32GB RAM ^| RTX 4060 8GB VRAM
echo ==============================================================================
echo.

cd /d "%~dp0"

REM 1. Kiem tra uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/6] Dang tai cong cu quan ly Python cuc nhanh uv...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

REM 2. Cai dat Python 3.12 va Tao Virtual Environment
echo [2/6] Dang khoi tao moi truong Python 3.12 sieu sach...
uv python install 3.12
uv venv env --python 3.12

REM 3. Cai dat PyTorch CUDA 12.8 cho RTX 4060
echo [3/6] Dang cai dat PyTorch 2.x voi CUDA 12.8 Acceleration cho RTX 4060...
uv pip install --python env\Scripts\python.exe torch torchaudio --index-url https://download.pytorch.org/whl/cu128

REM 4. Kiem tra va Clone Engine Applio-RVC
if not exist "..\Applio-RVC" (
    if not exist "Applio-RVC" (
        echo [4/6] Dang tai engine RVC Core tu GitHub...
        git clone https://github.com/IAHispano/Applio.git Applio-RVC
    )
)

REM 5. Cai dat cac thu vien Demucs, yt-dlp, Edge-TTS, FastAPI
echo [5/6] Dang cai dat AI Demucs GPU (Tach nhac nen), yt-dlp, Edge-TTS, FastAPI...
set "TARGET_ENV=env\Scripts\python.exe"
if exist "..\Applio-RVC\env\Scripts\python.exe" (
    set "TARGET_ENV=..\Applio-RVC\env\Scripts\python.exe"
)

uv pip install --python %TARGET_ENV% demucs yt-dlp edge-tts fastapi uvicorn python-multipart soundfile librosa onnxruntime-gpu einops local-attention

REM 6. Tai cac trong so AI Pretrained (RMVPE, ContentVec, HiFi-GAN 48k)
echo [6/6] Dang tai trong so AI Pretrained can thiet (1.9 GB)...
%TARGET_ENV% -c "import sys, os; sys.path.insert(0, os.path.abspath('Applio-RVC')); sys.path.insert(0, os.path.abspath('../Applio-RVC')); from rvc.lib.tools.prerequisites_download import prequisites_download_pipeline, ensure_pretrained; prequisites_download_pipeline(); ensure_pretrained('HiFi-GAN', 48000)"

echo.
echo ==============================================================================
echo [THANH CONG] Toan bo he thong da san sang chay tren RTX 4060!
echo Hay chay file 'start_studio.bat' de mo giao dien Web Dashboard.
echo ==============================================================================
echo.
pause
