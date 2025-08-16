@echo off
setlocal
title Rotoscopia Modular
REM Ruta de Python (ajusta si cambia)
set "PY=C:\Users\Ariel\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PY%" (
  echo No se encontró Python en: %PY%
  pause & exit /b 1
)
pushd "%~dp0"
echo === Comprobando dependencias ===
if exist requirements.txt (
  "%PY%" -m pip install --disable-pip-version-check -r requirements.txt
) else (
  echo (No hay requirements.txt, se continua...)
)
echo === Lanzando aplicacion ===
"%PY%" -c "from rotoscopia.main import main; main()" || goto :error
goto :end

:error
echo.
echo Hubo un error al ejecutar la app. Revisa mensajes arriba.
echo Presiona una tecla para cerrar.
pause >nul
goto :eof

:end
echo.
echo Ejecucion finalizada. Cierra esta ventana o presiona una tecla.
pause >nul
popd
endlocal
