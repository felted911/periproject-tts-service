#!/usr/bin/env python
"""
Load environment-specific configuration.
This script is used during CI/CD deployment to set up the correct environment variables.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def load_environment_config(env_name=None):
    """
    Load environment-specific configuration from the appropriate .env file.
    
    Args:
        env_name: The environment name (development, staging, production).
                 If None, uses the ENVIRONMENT variable or defaults to development.
    
    Returns:
        bool: True if successful, False if the environment file doesn't exist.
    """
    if env_name is None:
        env_name = os.getenv("ENVIRONMENT", "development")
    
    env_file = Path(__file__).parent / f"{env_name.lower()}.env"
    
    if not env_file.exists():
        print(f"Error: Environment file {env_file} not found", file=sys.stderr)
        return False
    
    print(f"Loading environment configuration from {env_file}")
    load_dotenv(env_file)
    return True

if __name__ == "__main__":
    env_arg = sys.argv[1] if len(sys.argv) > 1 else None
    success = load_environment_config(env_arg)
    
    if not success:
        sys.exit(1)
    
    print("Environment configuration loaded successfully")
    
    # Echo the current environment for verification
    print(f"Active environment: {os.getenv('ENVIRONMENT', 'Not set')}")
