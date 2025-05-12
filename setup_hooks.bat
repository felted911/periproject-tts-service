@echo off
REM Script to set up Git hooks on Windows

if not exist .git\hooks mkdir .git\hooks
copy /Y hooks\pre-push .git\hooks\pre-push

echo Git hooks have been set up successfully.
echo All tests will now run automatically before each push.
