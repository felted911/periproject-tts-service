@echo off
REM This script sets up VS Code development tools

echo Installing development dependencies...
call venv\Scripts\activate
pip install -r requirements-dev.txt

echo VS Code configuration is now complete.
echo Please open VS Code with the workspace file:
echo   File > Open Workspace from File... > peritest.code-workspace
echo Then reload the Python extension:
echo   Ctrl+Shift+P > Python: Restart Language Server
