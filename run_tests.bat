@echo off
REM Run unit tests
echo Running unit tests...
python -m pytest tests\unit -v

REM Run integration tests
echo Running integration tests...
python -m pytest tests\integration -v

REM Run coverage report if available
where pytest-cov >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Running coverage report...
    python -m pytest --cov=src\tts_service tests\
)

echo Tests completed.
