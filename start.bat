@echo off
REM Todoist Application Management Script
SETLOCAL

REM Change to the directory where the batch file is located
cd /d %~dp0

REM Check if Conda environment exists and activate it
if exist "%~dp0\conda" (
    call conda activate
) else (
    REM Activate the virtual environment
    call venv\Scripts\activate.bat
)

REM Define valid commands
set VALID_COMMANDS=start train test add-data

:menu
cls
echo ==============================
echo Todoist Application Management
echo ==============================
echo.
echo 1. Start Application (Flask + React)
echo 2. Start Application (Flask only)
echo 3. Train NLU Model
echo 4. Run Tests
echo 5. Add Sample Data
echo 6. Exit
echo.
set /p choice=Please select an option (1-6):

REM Handle menu selection
if "%choice%"=="1" (
    echo Starting Flask and React applications...

    REM Create necessary directories if they don't exist
    if not exist "ai_models" mkdir ai_models
    if not exist "db" mkdir db
    if not exist "backend" mkdir backend
    if not exist "frontend" mkdir frontend

    REM Install dependencies if needed
    pip install -r requirements.txt

    REM Initialize database
    python scripts/init_db.py

    REM Start the Flask backend in a new command window
    start cmd /k "cd /d %~dp0\backend && python app.py"

    REM Start the React frontend in a new command window
    start cmd /k "cd /d %~dp0\frontend && npm start"

    echo Todoist AI Assistant is running!
    echo Backend: http://localhost:5000
    echo Frontend: http://localhost:3000
    pause
    goto :menu
) else if "%choice%"=="2" (
    echo Starting Flask application...

    REM Create necessary directories if they don't exist
    if not exist "ai_models" mkdir ai_models
    if not exist "db" mkdir db
    if not exist "backend" mkdir backend

    REM Install dependencies if needed
    pip install -r requirements.txt

    REM Initialize database
    python scripts/init_db.py

    REM Start the Flask backend in a new command window
    start cmd /k "cd /d %~dp0\ python start.py"

    echo Todoist AI Assistant backend is running!
    echo Backend: http://localhost:5000
    pause
    goto :menu
) else if "%choice%"=="3" (
    echo Training NLU model...
    python start.py train
    pause
    goto :menu
) else if "%choice%"=="4" (
    echo Running tests...
    python start.py test
    pause
    goto :menu
) else if "%choice%"=="5" (
    echo Adding sample data...
    python start.py add-data
    pause
    goto :menu
) else if "%choice%"=="6" (
    goto :end
) else (
    echo Invalid selection. Please try again.
    timeout /t 2 >nul
    goto :menu
)

:end
ENDLOCAL
