"""
Example of how to load environment variables from .env file in Python

There are multiple ways to load environment variables from a .env file:
"""

import os
from dotenv import load_dotenv, find_dotenv, dotenv_values
from pathlib import Path


# Method 1: Load from default location (.env in current directory)
def load_env_basic():
    """Load .env file from current directory"""
    load_dotenv()

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    print(f"Email: {email}")
    print(f"Password: {'***' if password else None}")


# Method 2: Load from specific path
def load_env_from_path():
    """Load .env file from specific path"""
    # Relative path
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    # Or absolute path
    # env_path = Path('/server/local-ai-packaged/.env')
    # load_dotenv(dotenv_path=env_path)

    email = os.getenv("GARMIN_EMAIL")
    return email


# Method 3: Automatically find .env file in parent directories
def load_env_auto_find():
    """Automatically search for .env file in parent directories"""
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
    else:
        print("No .env file found")


# Method 4: Load as dictionary (doesn't set environment variables)
def load_env_as_dict():
    """Load .env file as a dictionary without setting environment variables"""
    config = dotenv_values(".env")

    # Access values from dict
    email = config.get("GARMIN_EMAIL")
    password = config.get("GARMIN_PASSWORD")

    return config


# Method 5: Override existing environment variables
def load_env_override():
    """Load .env and override existing environment variables"""
    load_dotenv(override=True)

    # This will replace any existing env vars with values from .env


# Method 6: Load multiple .env files
def load_multiple_env_files():
    """Load multiple .env files (later files override earlier ones)"""
    load_dotenv('.env')  # Load base config
    load_dotenv('.env.local', override=True)  # Override with local config
    load_dotenv('.env.production', override=True)  # Override with production config


# Method 7: Load in tests with specific path
def load_env_for_tests():
    """Load .env file for tests from parent directory"""
    # Get the directory of the current file
    current_dir = Path(__file__).parent

    # Go up to parent directories to find .env
    env_path = current_dir.parent.parent / '.env'

    if env_path.exists():
        load_dotenv(env_path)
        return True
    return False


# Method 8: Context manager pattern (for tests)
def load_env_context_manager():
    """Use context manager to temporarily set environment variables"""
    from unittest.mock import patch

    # This is useful for testing without needing real credentials
    with patch.dict(os.environ, {
        "GARMIN_EMAIL": "test@example.com",
        "GARMIN_PASSWORD": "test_password"
    }):
        # Environment variables are set within this block
        email = os.getenv("GARMIN_EMAIL")
        print(f"Mocked email: {email}")

    # Environment variables are restored after exiting the block


# Method 9: Load with validation
def load_env_with_validation():
    """Load .env file and validate required variables exist"""
    load_dotenv()

    required_vars = ["GARMIN_EMAIL", "GARMIN_PASSWORD"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return {var: os.getenv(var) for var in required_vars}


# Example usage in your application
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Access them
    garmin_email = os.getenv("GARMIN_EMAIL")
    garmin_password = os.getenv("GARMIN_PASSWORD")

    # With default value
    garmin_port = os.getenv("GARMIN_PORT", "3333")

    print(f"Loaded configuration:")
    print(f"  Email: {garmin_email}")
    print(f"  Password: {'***' if garmin_password else 'Not set'}")
    print(f"  Port: {garmin_port}")

