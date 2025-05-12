@echo off
REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Set environment variables
set PYTHONPATH=%CD%
set ENVIRONMENT=development
set API_HOST=localhost
set API_PORT=8000
set LOG_LEVEL=INFO

REM Run the application
cd src
python main.py
