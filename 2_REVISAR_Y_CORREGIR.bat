@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
%PY% --version >nul 2>nul || (echo No encontre Python. Usa HMJ_Kit.exe o instala Python 3 desde python.org ^(marca "Add Python to PATH"^). & pause & exit /b)
rem Arrastra tu CSV (o una carpeta de partes) sobre este .bat. Sin nada: revisa el CSV de trabajo.
%PY% herramientas\hmj_kit.py revisar %*
echo.
pause
