@echo off
setlocal enabledelayedexpansion

REM Change to script directory
cd /d "%~dp0"

REM Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.11 or newer from https://www.python.org/
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11 or newer is required'" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python 3.11 or newer is required
    echo Current Python version:
    python --version
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Virtual environment not found! Creating one...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Installing dependencies...
    call venv\Scripts\activate
    pip install --upgrade --requirement requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Virtual environment found. Activating...
)

REM Activate virtual environment
call venv\Scripts\activate
if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

REM Define valid commands
set VALID_COMMANDS=start train test add-data

REM If command is provided, execute it directly
if not "%1"=="" (
    REM Validate command
    echo %VALID_COMMANDS% | findstr /i "\<%1\>" >nul
    if errorlevel 1 (
        echo Error: Invalid command '%1'
        echo.
        echo Valid commands are: %VALID_COMMANDS%
        pause
        goto :end
    )

    REM Execute the command
    echo Running command: %1
    echo.
    python start.py %1

    if errorlevel 1 (
        echo Error: Command execution failed
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
echo.
echo 1. Start Application
echo 2. Train NLU Model
echo 3. Run Tests
echo 4. Add Sample Data
echo 5. Exit
echo.
set /p choice=Please select an option (1-5):

REM Handle menu selection
if "%choice%"=="1" (
    echo Starting application...
    python start.py start
    pause
    goto :menu
) else if "%choice%"=="2" (
    echo Training NLU model...
    python start.py train
    pause
    goto :menu
) else if "%choice%"=="3" (
    echo Running tests...
    python start.py test
    pause
    goto :menu
) else if "%choice%"=="4" (
    echo Adding sample data...
    python start.py add-data
    pause
    goto :menu
) else if "%choice%"=="5" (
    goto :end
) else (
    echo Invalid selection. Please try again.
    timeout /t 2 >nul
    goto :menu
)

:end
ENDLOCAL
