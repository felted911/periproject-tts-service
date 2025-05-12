#!/bin/bash

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit -v

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration -v

# Run coverage report
if command -v pytest-cov &> /dev/null; then
    echo "Running coverage report..."
    python -m pytest --cov=src/tts_service tests/
fi

echo "Tests completed."
