@echo off
REM This script installs dependencies, cleans up previous attempt, and runs the Peri TTS Service

echo Cleaning up previous attempt...
IF EXIST "venv" (
    echo Removing old virtual environment...
    rd /s /q venv
)

echo Creating new virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Downloading model files...
python -m src.utils.download_models --model-type int8

echo Starting the service...
set PYTHONPATH=%CD%
python src\main.py
