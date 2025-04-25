import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Feedly configuration
CLIENT_ID = os.getenv('FEEDLY_CLIENT_ID')
CLIENT_SECRET = os.getenv('FEEDLY_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('FEEDLY_REFRESH_TOKEN')
STREAM_ID = os.getenv('FEEDLY_STREAM_ID')

# Constants
DEFAULT_DAYS = 7

def check_environment_variables():
    """Check if all required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'FEEDLY_CLIENT_ID',
        'FEEDLY_CLIENT_SECRET',
        'FEEDLY_REFRESH_TOKEN',
        'FEEDLY_STREAM_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please check your .env file or environment variables."
        ) 