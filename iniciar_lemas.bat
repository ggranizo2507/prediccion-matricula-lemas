@echo off
rem ============================================================================
rem  Continuidad estudiantil LEMAS - modo institucional (solo en este equipo)
rem  Doble clic para abrir la aplicacion. Cierre esta ventana para terminarla.
rem  Requisito (una sola vez): Python 3.11 o superior de python.org, instalado
rem  con la opcion "Add python.exe to PATH". La primera ejecucion instala lo demas.
rem ============================================================================
setlocal
cd /d "%~dp0"
title Continuidad estudiantil LEMAS - modo institucional

if not exist "app\app.py" goto :sin_archivos

rem --- 1. Buscar un Python real (3.11 o superior) -----------------------------
rem Windows trae un acceso falso llamado "python" que solo abre la tienda de
rem Microsoft: por eso no basta con que exista, hay que comprobar que funciona.
set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto :preparar
python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto :preparar
goto :sin_python

rem --- 2. Crear el entorno de la aplicacion (solo la primera vez) -------------
:preparar
if exist ".venv\Scripts\python.exe" goto :comprobar
echo Preparando la aplicacion por primera vez. Puede tardar unos minutos...
%PY% -m venv .venv
if errorlevel 1 goto :error_entorno

rem --- 3. Instalar los componentes si faltan ----------------------------------
:comprobar
".venv\Scripts\python.exe" -c "import streamlit, openpyxl, sklearn, plotly, optuna, yaml" >nul 2>nul
if not errorlevel 1 goto :iniciar
echo Instalando los componentes de la aplicacion. Se necesita internet...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r app\requirements.txt
if errorlevel 1 goto :error_instalacion

rem --- 4. Abrir la aplicacion, solo en este equipo ----------------------------
:iniciar
set LEMAS_MODO=institucional
echo.
echo Abriendo la aplicacion en http://localhost:8501
echo Los datos se procesan solo en este equipo. No cierre esta ventana mientras la usa.
echo.
".venv\Scripts\python.exe" -m streamlit run app\app.py --server.address 127.0.0.1 --server.port 8501 --server.showEmailPrompt false --browser.gatherUsageStats false
goto :fin

:sin_archivos
echo.
echo No se encuentra la aplicacion junto a este archivo.
echo Descomprima primero la carpeta completa del proyecto y abra iniciar_lemas.bat
echo desde esa carpeta. No lo abra desde dentro del archivo .zip.
goto :pausa

:sin_python
echo.
echo Este equipo no tiene Python 3.11 o superior.
echo.
echo   1. Entre a https://www.python.org/downloads/windows/
echo   2. Descargue el instalador de Windows de 64 bits. Se recomienda Python 3.12.
echo   3. En la primera pantalla marque "Add python.exe to PATH" y pulse "Install Now".
echo   4. Cierre esta ventana y vuelva a abrir iniciar_lemas.bat
echo.
echo Nota: no use la version de la tienda de Microsoft.
goto :pausa

:error_entorno
echo.
echo No se pudo crear el entorno de la aplicacion.
echo Borre la carpeta .venv si existe, reinstale Python desde python.org
echo y vuelva a abrir iniciar_lemas.bat
goto :pausa

:error_instalacion
echo.
echo No se pudieron instalar los componentes.
echo Revise la conexion a internet y vuelva a abrir iniciar_lemas.bat
echo Si el problema continua, borre la carpeta .venv y vuelva a intentar.
goto :pausa

:pausa
echo.
pause
endlocal
exit /b 1

:fin
endlocal
