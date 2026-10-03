@echo off
echo ============================================================
echo   Starting AI Business Agent - full stack
echo ============================================================
echo.
echo [1/2] Launching ComfyUI in WSL (a new window will open)...
echo       Wait for: "To see the GUI go to: http://127.0.0.1:8188"
echo       Leave that window open.
echo.

start "ComfyUI (WSL)" wsl.exe -d Ubuntu -e bash -lc "cd ~/ComfyUI && source .venv/bin/activate && python main.py --cpu"

echo [2/2] Waiting 20 seconds for ComfyUI to boot...
timeout /t 20 /nobreak >nul

echo       Opening launcher...
cd /d "%~dp0"
python launcher.py

if errorlevel 1 pause