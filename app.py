import streamlit as st
import pandas as pd
from datetime import datetime
from main import fetch_and_process_articles, DEFAULT_DAYS
from rank_openai import generate_linkedin_post

# Page configuration
st.set_page_config(
    page_title="WarpzoneAI - AI Gaming Intelligence",
    page_icon="🎮",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .article-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .article-title {
        color: #1f1f1f;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .article-meta {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .article-score {
        color: #0066cc;
        font-weight: bold;
    }
    .article-bullets {
        margin: 1rem 0;
        line-height: 1.6;
        color: #333;
    }
    .article-bullets p {
        margin-bottom: 0.5rem;
    }
    .article-bullets br {
        display: block;
        content: "";
        margin-top: 0.5rem;
    }
    .article-bullets .bullet-point {
        display: block;
        margin-bottom: 0.5rem;
    }
    .sidebar-content {
        padding: 1rem;
    }
    .page-description {
        color: #666;
        font-style: italic;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .linkedin-post {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #0a66c2;
    }
    .linkedin-post-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .copy-button {
        background-color: #0a66c2;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        float: right;
        margin-top: 1rem;
    }
    .copy-button:hover {
        background-color: #004182;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .feedly-link {
        display: inline-block;
        padding: 8px 16px;
        background-color: #2bb24c;
        color: white !important;
        text-decoration: none;
        border-radius: 5px;
        margin-top: 1rem;
        font-weight: 500;
        transition: background-color 0.2s ease;
    }

    .feedly-link:hover {
        background-color: #249540;
        text-decoration: none;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

def format_date(date_str):
    """Format date string to a more readable format."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date.strftime('%B %d, %Y')
    except:
        return date_str

def display_article(article, show_linkedin_button=False):
    """Display an article in a card format."""
    # Format bullet points with proper line breaks
    bullet_points = article.get('Bullet_Points', '')
    if bullet_points and isinstance(bullet_points, str):
        formatted_bullets = []
        for line in bullet_points.split('\n'):
            if line.strip():
                if line.startswith('●'):
                    formatted_bullets.append(f'<div class="bullet-point">{line}</div>')
                else:
                    formatted_bullets.append(f'<div>{line}</div>')
        bullet_points_html = '\n'.join(formatted_bullets)
    else:
        bullet_points_html = f"<p>{article['Summary'][:300]}...</p>"

    # Generate unique key for this article's LinkedIn post
    article_key = f"linkedin_{article['URL']}"

    st.markdown(f"""
        <div class="article-card">
            <div class="article-title">{article['Title']}</div>
            <div class="article-meta">
                Published: {format_date(article['Publication Date'])} | 
                Score: <span class="article-score">{article['GPT_Pertinence']}/10</span>
            </div>
            <div class="article-bullets">
                {bullet_points_html}
            </div>
            <a href="{article['URL']}" target="_blank">Read more →</a>
        </div>
    """, unsafe_allow_html=True)

    # Add LinkedIn post generation button if requested
    if show_linkedin_button:
        # Initialiser le dictionnaire dans session_state s'il n'existe pas
        if 'linkedin_posts' not in st.session_state:
            st.session_state.linkedin_posts = {}

        if st.button("🔄 Generate LinkedIn Post", key=article_key):
            with st.spinner("Generating LinkedIn post..."):
                post_content = generate_linkedin_post(article)
                st.session_state.linkedin_posts[article_key] = post_content
                st.success("LinkedIn post generated!")

        # Display the generated post if it exists
        if article_key in st.session_state.linkedin_posts:
            display_linkedin_post(article, st.session_state.linkedin_posts[article_key])

def display_linkedin_post(article, post_content):
    """Display a LinkedIn post with copy button."""
    # Create a container for the post
    post_container = st.container()
    
    with post_container:
        # Display the post content
        st.markdown(f"""
            <div class="linkedin-post">
                <div class="linkedin-post-header">
                    <h3>LinkedIn Post for: {article['Title']}</h3>
                </div>
                <p style="white-space: pre-line">{post_content}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Add the copy button using Streamlit's native button
        if st.button("📋 Copy to Clipboard", key=f"copy_{article['URL']}"):
            st.write("Copied to clipboard!")
            st.code(post_content, language=None)

def main():
    # Initialize session state for articles and LinkedIn posts
    if 'articles_df' not in st.session_state:
        st.session_state.articles_df = None
    if 'linkedin_posts' not in st.session_state:
        st.session_state.linkedin_posts = {}
    if 'days_to_fetch' not in st.session_state:
        st.session_state.days_to_fetch = DEFAULT_DAYS

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # Logo and title
        st.title("🎮 WarpzoneAI")
        st.markdown("### AI Gaming Intelligence")
        
        # Navigation
        page = st.radio(
            "Select View",
            ["🌟 Top Stories", "📰 Trending Articles", "💼 LinkedIn Posts"],
            index=0
        )
        
    
        # Days selector
        days_to_fetch = st.slider(
            "Number of days to fetch",
            min_value=1,
            max_value=10,
            value=st.session_state.days_to_fetch,
            help="Select how many days of articles to fetch"
        )
        
        # Update session state if days changed
        if days_to_fetch != st.session_state.days_to_fetch:
            st.session_state.days_to_fetch = days_to_fetch
            st.session_state.articles_df = None  # Reset articles when days change
            st.session_state.linkedin_posts = {}  # Reset LinkedIn posts
        
        # Fetch articles button
        if st.button("🔍 Fetch New Articles"):
            try:
                # Create containers for different progress messages
                init_container = st.empty()
                feedly_container = st.empty()
                processing_container = st.empty()
                
                # Initialize
                init_container.info("🔄 Initializing article fetch...")
                st.session_state.articles_df = None
                st.session_state.linkedin_posts = {}
                
                # Fetch articles with progress updates
                feedly_container.info("📡 Connecting to Feedly API...")
                st.session_state.articles_df = fetch_and_process_articles(
                    days_to_fetch=st.session_state.days_to_fetch,
                    progress_callback=lambda msg: feedly_container.info(msg)
                )
                
                # Clear progress containers
                init_container.empty()
                feedly_container.empty()
                processing_container.empty()
                
                # Show success message
                st.success(f'✅ Successfully fetched {len(st.session_state.articles_df)} articles from the last {st.session_state.days_to_fetch} days!')
            except Exception as e:
                st.error(f"❌ Error fetching articles: {str(e)}")
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content
    st.markdown("""
        ## Mobile Gaming & AI News
        Tracking the intersection of Mobile Gaming and AI technology
    """)
    
    # Display content based on selection
    if st.session_state.articles_df is None:
        st.info("👈 Click 'Fetch New Articles' in the sidebar to load articles")
    else:
        df = st.session_state.articles_df
        
        if page == "🌟 Top Stories":
            st.subheader("Top Stories")
            st.markdown(f"""
                <div class="page-description">
                    📊 Our AI has identified these as the most relevant stories in mobile gaming and AI from the last {st.session_state.days_to_fetch} days. 
                    These articles represent breakthrough innovations, significant market moves, and strategic developments 
                    at the intersection of mobile gaming and artificial intelligence.
                    <br><br>
                    <a href="https://feedly.com/i/collection/content/user/ccfb539c-94d7-426e-abc7-5e528ce47a9f/category/6b673888-9bd0-4e9d-88f0-58bb327ae836" 
                       target="_blank" 
                       class="feedly-link">
                        📰 View all articles on Feedly →
                    </a>
                </div>
            """, unsafe_allow_html=True)
            
            #top_articles = df.sort_values('GPT_Pertinence', ascending=False).head(5)  # Get top 5 articles
            top_articles = df[df['GPT_Pertinence'] > 7].head(5)

            for _, article in top_articles.iterrows():
                display_article(article)
                
        elif page == "📰 Trending Articles":
            st.subheader("Trending Articles")
            st.markdown(f"""
                <div class="page-description">
                    🔥 High-impact articles from the last {st.session_state.days_to_fetch} days that are shaping the future of AI in gaming. 
                    These stories have scored above 7/10 in relevance to mobile gaming and AI integration, 
                    offering valuable insights into industry trends and opportunities.
                </div>
            """, unsafe_allow_html=True)
            
            trending_articles = df[df['GPT_Pertinence'] > 7].iloc[5:]  # Get articles scored > 7, excluding top 5
            
            if len(trending_articles) == 0:
                st.info("No trending articles found at the moment.")
            else:
                for _, article in trending_articles.iterrows():
                    display_article(article, show_linkedin_button=True)
        
        else:  # LinkedIn Posts
            st.subheader("LinkedIn Posts")
            st.markdown(f"""
                <div class="page-description">
                    💡 AI-generated LinkedIn posts optimized for maximum impact, based on our top stories from the last {st.session_state.days_to_fetch} days. 
                    Each post is crafted to position WarpzoneAI as a thought leader in the AI Gaming space, highlighting key insights 
                    and strategic implications.
                </div>
            """, unsafe_allow_html=True)
            
            top_articles = df[df['GPT_Pertinence'] > 7].head(5)  # Get top key stories
            
            with st.spinner('Generating LinkedIn posts...'):
                for _, article in top_articles.iterrows():
                    article_id = article['URL']  # Use URL as unique identifier
                    
                    # Generate post if not already generated
                    if article_id not in st.session_state.linkedin_posts:
                        try:
                            post_content = generate_linkedin_post(article)
                            st.session_state.linkedin_posts[article_id] = post_content
                        except Exception as e:
                            st.error(f"Error generating LinkedIn post: {str(e)}")
                            continue
                    
                    # Display the post using display_linkedin_post instead of display_article
                    display_linkedin_post(article, st.session_state.linkedin_posts[article_id])

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            WarpzoneAI - Powered by AI for the Future of Gaming
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 