# Development Environment Setup Guide

This document provides a step-by-step guide for setting up the development environment for the Peri TTS Python services. Following these instructions will ensure that all developers have a consistent environment for working on the project.

## Prerequisites

Before beginning, ensure you have the following installed on your system:

- **Python 3.8+** - Required for running the Python services
- **Git** - Required for version control
- **VS Code** (recommended) or your preferred IDE
- **Docker** (optional) - For containerized development

## Python Environment Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/peritest.git
cd peritest
```

### 2. Set Up Virtual Environment

It's recommended to use a virtual environment for Python development to isolate dependencies.

```bash
# Navigate to the Python directory
cd python

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install project dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Install Kokoro TTS

```bash
# Install Kokoro TTS
pip install kokoro

# Install espeak-ng (required for Kokoro TTS)
# On Windows:
# Download and install from https://github.com/espeak-ng/espeak-ng/releases
# On macOS:
brew install espeak-ng
# On Ubuntu/Debian:
sudo apt-get install espeak-ng
```

### 5. Configure Environment Variables

Create a `.env` file in the Python directory with the following variables:

```
# Development environment variables
DEBUG=True
LOG_LEVEL=DEBUG
CACHE_DIR=./cache
MODEL_DIR=./models
VOICES_DIR=./voices
PORT=8000
HOST=0.0.0.0
```

## IDE Setup

### VS Code Configuration

If you're using VS Code (recommended), here are some helpful settings:

1. **Install recommended extensions**:
   - Python
   - Pylance
   - Python Test Explorer
   - Python Docstring Generator
   - YAML
   - Docker

2. **Configure workspace settings**:

Create a `.vscode/settings.json` file with the following content:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/python/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

### PyCharm Configuration (Alternative)

If you're using PyCharm:

1. Open the `peritest` folder as a project
2. Go to `File > Settings > Project: peritest > Python Interpreter`
3. Add the virtual environment as an interpreter
4. Configure pytest as the test runner

## Model and Voice Setup

### 1. Download Test Models

```bash
# Create models directory
mkdir -p models

# Download a test model (placeholder command)
python -m scripts.download_test_model
```

### 2. Set Up Voice Files

```bash
# Create voices directory
mkdir -p voices

# Download test voice files (placeholder command)
python -m scripts.download_test_voices
```

## Running the Services

### Start the Development Server

```bash
# Ensure you're in the python directory with venv activated
cd python
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/api

# Run with coverage
pytest --cov=app
```

## Docker Development (Optional)

If you prefer to use Docker for development:

### 1. Build the Development Docker Image

```bash
# From the python directory
docker build -t peri-tts-dev -f Dockerfile.dev .
```

### 2. Run the Development Container

```bash
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd):/app \
  peri-tts-dev
```

## Troubleshooting Common Issues

### Issue: Module Not Found Errors

If you encounter "module not found" errors, ensure:
- Your virtual environment is activated
- All dependencies are installed
- You're running commands from the correct directory

### Issue: espeak-ng Not Found

If you see errors related to espeak-ng:
- Ensure espeak-ng is properly installed
- On Windows, make sure it's in your PATH
- Try reinstalling with `pip uninstall kokoro && pip install kokoro`

### Issue: Permission Denied for Cache or Model Directories

- Check that you have write permissions to the directories
- Try creating the directories manually before running the service

### Issue: FastAPI ImportError

- Ensure you have the correct version of FastAPI installed
- Check for conflicts with other installed packages

## Editor Integrations

### Pre-commit Hooks

Set up pre-commit hooks to ensure code quality before committing:

```bash
# Install pre-commit
pip install pre-commit

# Set up the git hooks
pre-commit install
```

### Linting and Formatting

Run linting and formatting manually:

```bash
# Format code with black
black app tests

# Run flake8 linting
flake8 app tests

# Type checking with mypy
mypy app
```

## Next Steps

After setting up your development environment:

1. Familiarize yourself with the project architecture
2. Run the example TTS service
3. Make a small change and run the tests
4. Submit a test pull request following the contribution guidelines

## Getting Help

If you encounter issues with your development environment:

- Check the project wiki for updates
- Ask in the #dev-setup channel on Slack
- File an issue in the GitHub repository

This setup guide should provide a consistent development environment for all team members working on the Peri TTS Python services.
