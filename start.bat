@echo off
REM Todoist Application Management Script

if "%1"=="" (
    echo Usage: start.bat [command]
    echo Available commands:
    echo   start     - Start the application
    echo   train     - Train the NLU model
    echo   test      - Run all tests
    echo   add-data  - Add sample data to the database
    goto :eof
)

python start.py %1
