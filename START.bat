@echo off
REM Officials Tracker Launcher
REM This script launches the Officials Tracker application

echo ================================================
echo    Officials Tracker
echo    Starting application...
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Checking dependencies...
pip install -q -r requirements.txt

REM Start the application
echo.
echo Starting Officials Tracker...
echo The application will open in your default web browser.
echo.
echo To stop the application, close this window or press Ctrl+C
echo.

streamlit run app.py

REM Deactivate virtual environment
deactivate
