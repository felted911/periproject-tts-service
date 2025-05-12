@echo off
echo Testing flake8 configuration...
flake8 --version
flake8 --help
echo.
echo Running flake8 on a single file to test configuration...
flake8 src\main.py
echo.
echo "If you see no error messages above, the .flake8 configuration is working correctly."
