@echo off
setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%\..\..
set PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
  echo Missing interpreter: "%PYTHON_EXE%"
  echo Create and initialize .venv first.
  exit /b 1
)

"%PYTHON_EXE%" "%PROJECT_ROOT%\scripts\install_windows_embedded_ocr.py" %*
exit /b %ERRORLEVEL%
