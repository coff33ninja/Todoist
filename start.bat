@echo off
REM Todoist Application Management Script
SETLOCAL

REM Change to the directory where the batch file is located
cd /d %~dp0

REM Check if Conda environment exists and activate it
if exist %~dp0\conda (
    call conda activate
) else (
    REM Activate the virtual environment
    call venv\Scripts\activate.bat
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
