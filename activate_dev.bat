@echo off
REM This script activates the development environment for the Peri TTS project

call venv\Scripts\activate

REM Set Python path
set PYTHONPATH=%CD%

REM Set development environment variables
set ENVIRONMENT=development
set API_HOST=localhost
set API_PORT=8000
set LOG_LEVEL=DEBUG

echo Development environment activated with PYTHONPATH=%PYTHONPATH%
echo Running in %ENVIRONMENT% mode, API will be available at %API_HOST%:%API_PORT%
echo Type 'deactivate' to exit the virtual environment

REM Provide some helpful commands
echo.
echo Available commands:
echo - python src\main.py             : Run the FastAPI application
echo - pytest tests\unit              : Run unit tests
echo - pytest tests\integration       : Run integration tests
