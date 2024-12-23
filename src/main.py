import json
from datetime import datetime
from src.config.config_loader import load_config, load_credentials
from src.scrapers.oshkosh_scraper import OshkoshScraper
from src.database.db_manager import (
    connect_to_db, create_event_table, add_event, get_events,
    calculate_post_timings, store_post_timings, get_due_posts, mark_post_as_executed, get_event_by_id
)
from src.bluesky.auth import authenticate
from src.bluesky.poster import post_event_to_bluesky

def main():
    # Load configuration
    config = load_config('config/config.json')
    credentials = load_credentials('config/credentials.json')
    
    # Initialize database
    connection = connect_to_db('database/events.db')
    create_event_table(connection)

    # Authenticate with Bluesky
    for account in credentials['accounts']:
        auth_token = authenticate(account['username'], account['access_token'])
        account['auth_token'] = auth_token

    # Initialize scraper
    oshkosh_scraper = OshkoshScraper(config['websites'][0])
    
    # Scrape events
    events = oshkosh_scraper.scrape()
    for event in events:
        event_id = add_event(connection, event['url'], event['date'])
        post_timings = calculate_post_timings(event['date'])
        store_post_timings(connection, event_id, post_timings, credentials['accounts'][0]['username'])

    # Check for due posts
    due_posts = get_due_posts(connection)
    for post in due_posts:
        event = get_event_by_id(connection, post['event_id'])
        account = next(acc for acc in credentials['accounts'] if acc['username'] == post['account_id'])
        post_event_to_bluesky(event, account)
        mark_post_as_executed(connection, post['id'])

if __name__ == "__main__":
    main()