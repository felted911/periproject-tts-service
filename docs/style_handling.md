# Style Handling in Dev Environment CI/CD

This document explains how code style issues are handled in the CI/CD pipeline for the development environment.

## Current Approach

Since this project is for development purposes only and won't go to production, we've configured the CI/CD pipeline to be more permissive with style issues:

1. **Validation Steps Continue on Error**: The linting, formatting, and type-checking steps are configured with `continue-on-error: true`, allowing the pipeline to proceed even if these checks fail.

2. **Style Configuration Files**:
   - `.flake8`: Ignores common style issues like line length, whitespace, unused imports, etc.
   - `pyproject.toml`: Configures black with a more permissive line length (120 characters).

## Future Code Quality Improvements

If you wish to improve code quality in the future, consider:

1. **Gradually Fixing Issues**:
   - Run `black` locally to automatically fix many formatting issues
   - Address flake8 warnings systematically, starting with unused imports and variables

2. **Re-enabling Strict Checks**:
   - Once most issues are resolved, remove the `continue-on-error: true` settings
   - Gradually reduce the ignored rules in the `.flake8` configuration

## Running Style Checks Locally

You can run the style checks locally to see the issues and fix them:

```bash
# Run flake8 linting
flake8 src tests

# Run black formatting check
black --check src tests

# Run type checking
mypy src
```

To automatically fix formatting issues, run:

```bash
# Auto-format code with black
black src tests
```
