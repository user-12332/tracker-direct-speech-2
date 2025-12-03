#!/bin/bash
# Officials Tracker Launcher (Mac/Linux)
# This script launches the Officials Tracker application

echo "================================================"
echo "   Officials Tracker"
echo "   Starting application..."
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo ""
    echo "Please install Python from: https://www.python.org/downloads/"
    echo "Or use: brew install python3 (on Mac)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Start the application
echo ""
echo "Starting Officials Tracker..."
echo "The application will open in your default web browser."
echo ""
echo "To stop the application, press Ctrl+C"
echo ""

streamlit run app.py

# Deactivate virtual environment
deactivate
