@echo off
rem ============================================================================
rem  Continuidad estudiantil LEMAS - modo institucional (solo en este equipo)
rem  Doble clic para abrir la aplicacion. Cierre esta ventana para terminarla.
rem  Requisito (una sola vez): Python 3.11 o superior, instalado con la opcion
rem  "Add python.exe to PATH". La primera ejecucion instala lo necesario.
rem ============================================================================
setlocal
cd /d "%~dp0"
title Continuidad estudiantil LEMAS - modo institucional

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python. Instale Python 3.11 o superior desde python.org
    echo y marque la opcion "Add python.exe to PATH". Luego vuelva a abrir este archivo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Preparando la aplicacion por primera vez. Puede tardar unos minutos...
    python -m venv .venv
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r app\requirements.txt
    if errorlevel 1 goto :error
)

set LEMAS_MODO=institucional
echo.
echo Abriendo la aplicacion en http://localhost:8501
echo Los datos se procesan solo en este equipo. No cierre esta ventana mientras la usa.
echo.
".venv\Scripts\python.exe" -m streamlit run app\app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
goto :fin

:error
echo.
echo No se pudo completar la instalacion. Revise la conexion a internet y vuelva a intentar.
pause
exit /b 1

:fin
endlocal
