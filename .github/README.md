# CI/CD Configuration

This directory contains GitHub Actions workflows for the Peri TTS Service project.

## Dev-Only Deployment

The workflows in this repository are configured to deploy **ONLY** to the development environment. This is an intentional design decision as this code base is meant for development purposes only.

## Available Workflows

- `dev-deploy.yml`: Validates, tests, builds, and deploys the code to the development environment.

## Deployment Process

1. Push code to the `develop` branch
2. GitHub Actions will automatically:
   - Run code validation (linting, formatting checks)
   - Run tests
   - Build Docker image
   - Deploy to development environment

## Restrictions

To prevent accidental deployment to production:

1. The workflow is configured to only run on the `develop` branch
2. There is an explicit check to prevent running on `main`, `master`, or `production` branches
3. No production deployment jobs are defined in any workflow

## Modifying Deployment Configuration

If you need to change how deployment works:

1. Edit the `.github/workflows/dev-deploy.yml` file
2. Update the deployment steps in the `deploy-dev` job
3. Make sure to keep the branch restrictions that prevent production deployment

## Questions

If you have questions about the CI/CD configuration, please contact the DevOps team.
