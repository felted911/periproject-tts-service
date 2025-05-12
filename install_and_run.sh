#!/bin/bash
# This script installs dependencies, cleans up previous attempt, and runs the Peri TTS Service

echo "Cleaning up previous attempt..."
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

echo "Creating new virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Downloading model files..."
python -m src.utils.download_models --model-type int8

echo "Starting the service..."
export PYTHONPATH=$(pwd)
python src/main.py
