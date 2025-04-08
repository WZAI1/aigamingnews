import datetime
import pandas as pd
from bs4 import BeautifulSoup
from feedly import refresh_access_token, get_feedly_articles
from rank_openai import batch_gpt_scoring, generate_bullet_points_for_top_articles, DEFAULT_BATCH_SIZE
from typing import List, Dict, Any, Callable, Optional
import os
from dotenv import load_dotenv
from config import DEFAULT_DAYS

# Load environment variables
load_dotenv()

# Authentication parameters
CLIENT_ID = os.getenv('FEEDLY_CLIENT_ID')
CLIENT_SECRET = os.getenv('FEEDLY_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('FEEDLY_REFRESH_TOKEN')
STREAM_ID = os.getenv('FEEDLY_STREAM_ID')

# Feedly stream configuration
COUNT = 250

# Get initial access token
ACCESS_TOKEN, TOKEN_EXPIRY = refresh_access_token(REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET)

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

# Call this function at startup
check_environment_variables()

def clean_html_content(content):
    """Clean HTML content by removing HTML tags and extra whitespace."""
    if not isinstance(content, str) or not content.strip():
        return ''
    return BeautifulSoup(content, "html.parser").get_text().strip()

def extract_article_data(article):
    """Extract relevant information from a Feedly article."""
    # Get published timestamp with default value
    published = article.get('published')
    publication_date = (
        datetime.datetime.utcfromtimestamp(published / 1000).strftime('%Y-%m-%d %H:%M:%S')
        if published is not None
        else "No date available"
    )
    
    return {
        'Title': article.get('title'),
        'URL': article.get('alternate', [{}])[0].get('href'),
        'Content': article.get('fullContent'),
        'Author': article.get('author'),
        'Summary': article.get("summary", {}).get("content", ""),
        'Publication Date': publication_date,
        'Keywords': ', '.join(article.get('keywords', [])),
        'Mentioned Entities': ', '.join([entity.get('label') for entity in article.get('entities', [])]),
        'Score': {topic["label"]: topic["score"] for topic in article.get("commonTopics", []) if "score" in topic}
    }

def fetch_and_process_articles(
    days_to_fetch: int = 7,
    progress_callback: Optional[Callable[[str], None]] = None
) -> pd.DataFrame:
    """
    Fetch articles from Feedly and process them with GPT ranking.
    
    Args:
        days_to_fetch (int): Number of days to fetch articles for
        progress_callback (Optional[Callable[[str], None]]): Callback function to report progress
        
    Returns:
        pd.DataFrame: Processed articles with GPT rankings
    """
    def log_progress(msg: str) -> None:
        """Helper function to log progress using callback if available"""
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)
    
    try:
        # Fetch articles from Feedly
        articles = get_feedly_articles(
            stream_id=STREAM_ID,
            access_token=ACCESS_TOKEN,
            token_expiry=TOKEN_EXPIRY,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            days=days_to_fetch
        )
        
        if not articles:
            log_progress("No articles found.")
            return pd.DataFrame()
        
        # Convert to DataFrame and extract article data
        articles_data = [extract_article_data(article) for article in articles]
        df = pd.DataFrame(articles_data)
        
        # Remove duplicate articles based on title
        df = df.drop_duplicates(subset=['Title'], keep='first')
        
        # Clean HTML content
        df['Summary'] = df['Summary'].apply(clean_html_content)
        df['Content'] = df['Content'].apply(clean_html_content)
        
        # First phase: Score all articles
        log_progress("🤖 Starting article scoring...")
        df = batch_gpt_scoring(df, column='Summary')
        
        # Second phase: Generate bullet points for top 5 articles
        log_progress("📝 Generating bullet points for top articles...")
        df = generate_bullet_points_for_top_articles(df, column='Content', top_n=5)
        
        return df
        
    except Exception as e:
        log_progress(f"❌ Error in fetch_and_process_articles: {str(e)}")
        raise

if __name__ == "__main__":
    df_top = fetch_and_process_articles()
    print(df_top)


