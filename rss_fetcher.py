import feedparser
import json
from datetime import datetime
import os
import argparse
import requests
from bs4 import BeautifulSoup
import time

def fetch_rss_with_requests():
    """
    Fetch RSS feed using direct HTTP request
    """
    url = 'https://cointelegraph.com/editors_pick_rss'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/rss+xml,application/xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Use feedparser to parse the raw XML content
        feed = feedparser.parse(response.content)
        
        articles = []
        if hasattr(feed, 'entries'):
            for entry in feed.entries:
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published if hasattr(entry, 'published') else None,
                    'summary': entry.summary if hasattr(entry, 'summary') else None,
                    'tags': [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else [],
                    'source': 'editors_pick_rss'
                }
                articles.append(article)
        
        print(f"Found {len(articles)} articles in RSS feed")
        return articles
    except Exception as e:
        print(f"Error fetching RSS: {str(e)}")
        print(f"Response content (first 500 chars): {response.text[:500]}")
        return []

def fetch_hot_stories():
    """
    Fetch hot stories from Cointelegraph homepage using web scraping
    """
    url = "https://cointelegraph.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        hot_stories = []
        
        # Look for articles in news links
        news_links = soup.select("a[href*='/news/']")
        for link in news_links[:10]:
            title = link.get_text(strip=True)
            href = link['href']
            if title and href and href not in [s['link'] for s in hot_stories]:
                if not href.startswith('http'):
                    href = "https://cointelegraph.com" + href
                hot_stories.append({
                    'title': title,
                    'link': href,
                    'source': 'news_links'
                })
        
        return hot_stories
    except Exception as e:
        print(f"Error fetching hot stories: {str(e)}")
        return []

def main(date_override=None):
    """
    Main function to fetch both RSS and hot stories
    """
    # Fetch RSS feed articles
    articles = fetch_rss_with_requests()
    
    # Fetch hot stories
    hot_stories = fetch_hot_stories()
    
    # Create the output directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Use provided date or current date
    if date_override:
        try:
            datetime.strptime(date_override, '%Y-%m-%d')
            current_date = date_override
        except ValueError:
            print(f"Invalid date format: {date_override}. Using current date instead.")
            current_date = datetime.now().strftime('%Y-%m-%d')
    else:
        current_date = datetime.now().strftime('%Y-%m-%d')
    
    filename = f'data/cointelegraph_combined_{current_date}.json'
    
    # Save the articles and hot stories to a JSON file
    output_data = {
        'fetch_date': current_date,
        'fetch_timestamp': datetime.now().isoformat(),
        'editors_pick_articles': articles,
        'hot_stories': hot_stories,
        'metadata': {
            'num_editor_picks': len(articles),
            'num_hot_stories': len(hot_stories)
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f'Successfully saved {len(articles)} editor picks and {len(hot_stories)} hot stories to {filename}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch CoinTelegraph Editors Pick RSS feed and Hot Stories')
    parser.add_argument('--date', type=str, help='Override date (YYYY-MM-DD format)')
    args = parser.parse_args()
    
    main(args.date)