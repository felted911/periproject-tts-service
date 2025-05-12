#!/bin/bash

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH=$(pwd)
export ENVIRONMENT=development
export API_HOST=localhost
export API_PORT=8000
export LOG_LEVEL=INFO

# Run the application
cd src
python main.py
