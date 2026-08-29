@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Installing local Whisper dependencies...
py -m pip install --upgrade pip
py -m pip install -r requirements-whisper.txt
if errorlevel 1 (echo Installation failed.& pause & exit /b 1)
py -c "from faster_whisper import WhisperModel; print('faster-whisper installed successfully.')"
pause
