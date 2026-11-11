@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0iniciar.py" %*
) else (
    python "%~dp0iniciar.py" %*
)
if errorlevel 1 echo No se pudo iniciar. Revisa el mensaje de arriba.
pause
endlocal
