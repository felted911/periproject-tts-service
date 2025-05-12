#!/bin/bash
# Script to set up Git hooks on Linux/macOS

mkdir -p .git/hooks
cp hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "Git hooks have been set up successfully."
echo "All tests will now run automatically before each push."
