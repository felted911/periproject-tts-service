# TTS Service Deployment Guide

This guide explains how to deploy the TTS Service to the development environment. **Note that this service is intentionally configured for development use only and should never be deployed to production.**

## CI/CD Pipeline Overview

We've implemented a GitHub Actions-based CI/CD pipeline that automatically deploys changes to the development environment when you push code to the `develop` branch.

### Pipeline Stages

1. **Branch Check**: Ensures we're not accidentally deploying to production
2. **Code Validation**: Runs linting and formatting checks
3. **Testing**: Runs all tests to verify functionality
4. **Build**: Builds a Docker image for the service
5. **Deployment**: Deploys the Docker image to the development environment
6. **Verification**: Verifies the deployment is working correctly

## How to Deploy

### Automated Deployment

1. Make sure all your changes are tested and working locally
2. Commit your changes to the `develop` branch:

```bash
git checkout develop
git add .
git commit -m "Your descriptive commit message"
git push origin develop
```

3. GitHub Actions will automatically trigger the deployment workflow
4. Monitor the workflow progress in the GitHub Actions tab
5. Once completed, your changes will be available in the development environment

### Manual Deployment (if needed)

If you need to deploy manually (not recommended), you can:

1. Build the Docker image locally:

```bash
docker build -t tts-service:dev .
```

2. Run the service:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Environment Configuration

The development environment uses specific configuration values defined in `config/environments/development.env`. If you need to modify the development environment settings, update this file and then redeploy.

Key development settings:
- `ENVIRONMENT=development`
- `LOG_LEVEL=DEBUG`
- `KOKORO_USE_GPU=false`
- `RATE_LIMIT_ENABLED=false`

## Troubleshooting Deployments

### Common Issues

1. **Tests failing during CI/CD**: Fix all test failures locally before pushing again
2. **Docker build failing**: Check the GitHub Actions logs for details on the failure
3. **Deployment failing**: Verify your Docker configuration and the development server is accessible
4. **Service not starting**: Check the logs for errors:

```bash
# On the development server
docker logs peri-tts-service-dev
```

### Rollback Procedure

If you need to roll back to a previous version:

1. Find the Docker image tag of the previous working version in GitHub Packages
2. SSH into the development server
3. Update the Docker Compose file to use the previous version
4. Restart the service:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Monitoring

The dev deployment includes basic monitoring through:

1. The `/health` endpoint: Provides service health information
2. Docker logs: View logs with `docker logs peri-tts-service-dev`

## Security Considerations

Even though this is a development environment, follow these security practices:

1. Never commit secrets or credentials to the repository
2. Use environment variables for sensitive information
3. Keep the development environment isolated from production data
4. Regularly update dependencies to patch security vulnerabilities

## Remember: Development Only

This service is intended for development use only. The CI/CD pipeline has safeguards to prevent accidental deployment to production, including:

1. Branch restrictions that only allow deployment from the `develop` branch
2. Explicit checks that prevent running on `main`, `master`, or `production` branches
3. No production deployment jobs in the workflow

If you ever need to move this to production, a separate CI/CD pipeline and thorough security review would be required.
