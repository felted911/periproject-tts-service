# Git Hooks

This directory contains Git hooks that help maintain code quality. 

## Available Hooks

### pre-push

The pre-push hook runs all tests before pushing code to ensure only working code is pushed to the repository.

## Installation

To install the hooks, copy them to your local `.git/hooks` directory and make them executable:

### On Windows

```powershell
# Navigate to the project root
copy hooks\pre-push .git\hooks\pre-push
```

### On Linux/macOS

```bash
# Navigate to the project root
cp hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

## Skipping Hooks

If you need to skip the hooks for any reason (not recommended), you can use the `--no-verify` flag:

```bash
git push --no-verify
```

However, this should only be done in exceptional circumstances, as the hooks are designed to ensure code quality.
