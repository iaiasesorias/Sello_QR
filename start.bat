@echo off
set VENV_PATH=venv

if not exist %VENV_PATH%\Scripts\activate.bat (
    echo Entorno virtual no encontrado. Creando...
    python -m venv %VENV_PATH%
)

call %VENV_PATH%\Scripts\activate.bat

pip install -r requirements.txt

python src/main.py
pause