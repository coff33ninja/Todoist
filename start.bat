@echo off
REM Todoist Application Management Script with enforced virtual environment
SETLOCAL EnableDelayedExpansion

REM Change to the directory where the batch file is located
cd /d %~dp0

REM Define the virtual environment path
set VENV_PATH=%~dp0venv

REM Check if virtual environment exists; create it if it doesn’t
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo Virtual environment not found at %VENV_PATH%. Creating one now...
    python -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        echo Please ensure Python is installed and accessible.
        pause
        goto :end
    )
    echo Virtual environment created successfully.
)

REM Activate the virtual environment
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo Error: Failed to activate virtual environment at %VENV_PATH%.
    pause
    goto :end
)
echo Virtual environment activated: %VENV_PATH%

REM Define valid commands
set "VALID_COMMANDS=start train test add-data"

REM If command is provided, execute it directly
if not "%1"=="" (
    echo %VALID_COMMANDS% | findstr /i "\<%1\>" >nul
    if errorlevel 1 (
        echo Error: Invalid command '%1'
        echo.
        echo Valid commands are: %VALID_COMMANDS%
        pause
        goto :end
    )

    echo Running command: %1
    echo.
    python start.py %1
    if errorlevel 1 (
        echo Error: Command execution failed with error code %errorlevel%
        pause
    )
    goto :end
)

REM Interactive menu
:menu
cls
echo ==============================
echo Todoist Application Management
echo ==============================
echo Virtual environment: %VENV_PATH%
echo.
echo 1. Start Flask React Application (app.py)
echo 2. Start Flask Application (start.py)
echo 3. Train NLU Model
echo 4. Run Tests
echo 5. Add Sample Data
echo 6. Exit
echo.
set "choice="
set /p choice=Please select an option (1-6): 

REM Handle menu selection
if "!choice!"=="1" (
    echo Starting Flask React Application...
    REM Create necessary directories if they don't exist
    if not exist "ai_models" mkdir ai_models
    if not exist "db" mkdir db
    if not exist "backend" mkdir backend
    if not exist "frontend" mkdir frontend

    REM Install dependencies if needed
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install requirements.
        pause
        goto :menu
    )
    python -m spacy download en_core_web_sm
    if errorlevel 1 (
        echo Error: Failed to download SpaCy model.
        pause
        goto :menu
    )

    REM Initialize database
    python scripts/init_db.py
    if errorlevel 1 (
        echo Error: Failed to initialize database.
        pause
        goto :menu
    )

    REM Start the Flask backend
    start cmd /k python backend/app.py

    REM Open the frontend in the default browser
    timeout /t 2 >nul
    start frontend/index.html

    echo Todoist AI Assistant is running!
    echo Backend: http://localhost:5000
    echo Frontend: Open frontend/index.html in your browser
    pause
    goto :menu

) else if "!choice!"=="2" (
    echo Starting Flask Application using start.py...
    python start.py start
    if errorlevel 1 (
        echo Error: Failed to start Flask application.
        pause
    )
    pause
    goto :menu

) else if "!choice!"=="3" (
    echo Training NLU model...
    python start.py train
    if errorlevel 1 (
        echo Error: Failed to train NLU model.
        pause
    )
    pause
    goto :menu

) else if "!choice!"=="4" (
    echo Running tests...
    python start.py test
    if errorlevel 1 (
        echo Error: Failed to run tests.
        pause
    )
    pause
    goto :menu

) else if "!choice!"=="5" (
    echo Adding sample data...
    python start.py add-data
    if errorlevel 1 (
        echo Error: Failed to add sample data.
        pause
    )
    pause
    goto :menu

) else if "!choice!"=="6" (
    goto :end

) else (
    echo Invalid selection. Please try again.
    timeout /t 2 >nul
    goto :menu
)

:end
REM Deactivate the virtual environment (optional, explicit cleanup)
call deactivate 2>nul
echo Virtual environment deactivated.
ENDLOCAL
exit /b