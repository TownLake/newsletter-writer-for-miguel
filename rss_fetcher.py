import feedparser
import json
from datetime import datetime
import os
import argparse
import requests
from bs4 import BeautifulSoup

def fetch_hot_stories():
    """
    Fetch hot stories from Cointelegraph homepage using web scraping
    Returns:
        list: List of dictionaries containing hot stories
    """
    url = "https://cointelegraph.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.text, "html.parser")
        hot_stories_section = soup.find("section", {"class": "hot-stories"})
        
        if not hot_stories_section:
            print("Warning: Could not find the 'Hot Stories' section")
            return []
        
        hot_stories = []
        story_links = hot_stories_section.find_all("a", {"class": "post-card-inline__title-link"})
        
        for story in story_links:
            hot_stories.append({
                'title': story.text.strip(),
                'link': "https://cointelegraph.com" + story["href"],
                'source': 'hot_stories'
            })
        
        return hot_stories
    
    except requests.RequestException as e:
        print(f"Error fetching hot stories: {e}")
        return []

def fetch_rss(date_override=None):
    """
    Fetch RSS feed and hot stories, save to JSON file
    Args:
        date_override (str, optional): Date in YYYY-MM-DD format to override the current date
    """
    # Fetch the RSS feed
    feed = feedparser.parse('https://cointelegraph.com/editors_pick_rss')
    
    # Create a list to store the articles
    articles = []
    
    # Process each entry in the feed
    for entry in feed.entries:
        article = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary,
            'tags': [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else [],
            'source': 'editors_pick_rss'
        }
        articles.append(article)
    
    # Fetch hot stories
    hot_stories = fetch_hot_stories()
    
    # Create the output directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Use provided date or current date
    if date_override:
        try:
            # Validate date format
            datetime.strptime(date_override, '%Y-%m-%d')
            current_date = date_override
        except ValueError:
            print(f"Invalid date format: {date_override}. Using current date instead.")
            current_date = datetime.now().strftime('%Y-%m-%d')
    else:
        current_date = datetime.now().strftime('%Y-%m-%d')
    
    filename = f'data/cointelegraph_combined_{current_date}.json'
    
    # Save the articles and hot stories to a JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'fetch_date': current_date,
            'fetch_timestamp': datetime.now().isoformat(),
            'editors_pick_articles': articles,
            'hot_stories': hot_stories
        }, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully saved {len(articles)} editor picks and {len(hot_stories)} hot stories to {filename}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch CoinTelegraph Editors Pick RSS feed and Hot Stories')
    parser.add_argument('--date', type=str, help='Override date (YYYY-MM-DD format)')
    args = parser.parse_args()
    
    fetch_rss(args.date)