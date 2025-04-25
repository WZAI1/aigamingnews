import requests
import time
from typing import Tuple, List, Dict, Any
from urllib.parse import quote
from datetime import datetime, timedelta
from config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, STREAM_ID

# Constants
FEEDLY_API_BASE_URL = 'https://cloud.feedly.com/v3'
FEEDLY_AUTH_URL = 'https://api.feedly.com/v3/auth/token'
DEFAULT_TOKEN_EXPIRY = 3600  # seconds
DEFAULT_BATCH_SIZE = 100
DAYS_TO_FETCH = 7

class FeedlyAPIError(Exception):
    """Custom exception for Feedly API errors."""
    pass

def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Tuple[str, float]:
    """
    Refresh the access token using the refresh token.
    
    Args:
        refresh_token (str): The refresh token
        client_id (str): The client ID
        client_secret (str): The client secret
        
    Returns:
        Tuple[str, float]: A tuple containing the new access token and its expiry timestamp
        
    Raises:
        FeedlyAPIError: If the token refresh fails
    """
    try:
        payload = {
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
        }
        response = requests.post(FEEDLY_AUTH_URL, data=payload)
        response.raise_for_status()
        tokens = response.json()
        
        access_token = tokens['access_token']
        expires_in = tokens.get('expires_in', DEFAULT_TOKEN_EXPIRY)
        token_expiry = time.time() + expires_in
        
        print("🔑 Token refreshed successfully. Valid for", expires_in, "seconds.")
        return access_token, token_expiry
        
    except requests.exceptions.RequestException as e:
        raise FeedlyAPIError(f"Failed to refresh token: {str(e)}")
    
def get_feedly_articles(
    stream_id: str,
    access_token: str,
    token_expiry: float,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    days: int = DAYS_TO_FETCH
) -> List[Dict[str, Any]]:
    """
    Fetch articles from a Feedly stream for the specified number of days.
    Automatically refreshes the token if it expires.
    
    Args:
        stream_id (str): The ID of the Feedly stream
        access_token (str): The current access token
        token_expiry (float): The timestamp when the token expires
        refresh_token (str): The refresh token
        client_id (str): The client ID
        client_secret (str): The client secret
        days (int, optional): Number of days to fetch articles for. Defaults to 7.
        
    Returns:
        List[Dict[str, Any]]: List of article dictionaries
        
    Raises:
        FeedlyAPIError: If the API request fails
    """
    try:
        print(f"📅 Fetching articles from the last {days} days...")
        cutoff_time = int((time.time() - days * 24 * 60 * 60) * 1000)
        all_articles = []
        continuation = None
        batch_count = 0

        while True:
            if time.time() >= token_expiry:
                print("⏰ Token expired, refreshing...")
                access_token, token_expiry = refresh_access_token(refresh_token, client_id, client_secret)

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            params = {
                'streamId': stream_id,
                'newerThan': cutoff_time,
                'count': DEFAULT_BATCH_SIZE
            }
            if continuation:
                params['continuation'] = continuation

            response = requests.get(
                f'{FEEDLY_API_BASE_URL}/streams/contents',
                headers=headers,
                params=params
            )

            if response.status_code == 401:
                print("🔐 Token expired (401), refreshing...")
                access_token, token_expiry = refresh_access_token(refresh_token, client_id, client_secret)
                continue

            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            all_articles.extend(items)
            batch_count += 1
            print(f"📥 Batch {batch_count}: Retrieved {len(items)} articles")

            continuation = data.get('continuation')
            if not continuation:
                break

        print(f"✅ Successfully fetched {len(all_articles)} articles in {batch_count} batches from the last {days} days.")
        return all_articles

    except Exception as e:
        print(f"❌ Error in get_feedly_articles: {str(e)}")
        raise
