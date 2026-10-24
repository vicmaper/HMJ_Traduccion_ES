@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
%PY% --version >nul 2>nul || (echo No encontre Python. Usa HMJ_Kit.exe o instala Python 3 desde python.org ^(marca "Add Python to PATH"^). & pause & exit /b)
echo Instalando lo que necesita el kit (numpy, opencv, pillow, fonttools, imageio-ffmpeg)...
%PY% -m pip install --upgrade -r requirements.txt
echo.
echo === TERMINADO ===
pause
