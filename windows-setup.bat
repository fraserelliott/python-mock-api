@echo off

echo Creating virtual environment...
python -m venv venv || (
    echo Python not found.
    exit /b 1
)
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt || (
    echo pip install failed
    exit /b 1
)

echo Creating launcher script...
(
echo @echo off
echo call venv\Scripts\activate
echo python gui.py
) > run_gui.bat

echo Setup complete. Run run_gui.bat to start the app.