import json
import argparse
import os
from datetime import datetime
from src.config.config_loader import load_config, load_credentials
from src.scrapers.oshkosh_scraper import OshkoshScraper
from src.scrapers.winnebago_scraper import WinnebagoScraper
from src.database.db_manager import (
    connect_to_db, create_event_table, create_publication_schedule_table, add_event, get_events,
    calculate_post_timings, store_post_timings, get_due_posts, mark_post_as_executed, get_event_by_id
)
from src.bluesky.auth import authenticate
from src.bluesky.poster import post_event_to_bluesky, dry_run

def main():
    # Load configuration
    config = load_config('config/config.json')
    credentials = load_credentials()
    
    # Initialize database
    connection = connect_to_db('database/events.db')
    create_event_table(connection)
    create_publication_schedule_table(connection)

    # Authenticate with Bluesky
    for account in credentials['accounts']:
        auth_token = authenticate(account['username'], account['password'])
        account['auth_token'] = auth_token

    # Initialize scraper
    for website in config['websites']:
        account_username = website['account_username']
        account = next(acc for acc in credentials['accounts'] if acc['username'] == account_username)
        if website['name'] == 'OshkoshEvents':
            scraper = OshkoshScraper(website)
        elif website['name'] == 'WinnebagoEvents':
            scraper = WinnebagoScraper(website)
        
        # Scrape events
        events = scraper.scrape()
        for event in events:
            event_id = add_event(
                connection,
                event['title'],
                datetime.fromisoformat(event['start_date']),
                datetime.fromisoformat(event['end_date']),
                event['url'],
                event['description'],
                event['location'],
                event['address'],
                event['city'],
                event['region'],
                account_username,
                website['name'],
                website['hashtags']
            )
            post_timings = calculate_post_timings(datetime.fromisoformat(event['start_date']))
            store_post_timings(connection, event_id, post_timings, account_username)

    # Check for due posts
    due_posts = get_due_posts(connection)
    for post in due_posts:
        event = get_event_by_id(connection, post['event_id'])
        account = next(acc for acc in credentials['accounts'] if acc['username'] == post['account_username'])
        if os.getenv('PROD'):
            post_event_to_bluesky(event, account)
        else:
            dry_run(event)
        mark_post_as_executed(connection, post['id'])

def dry_run():
    # Load configuration
    config = load_config('config/config.json')

    # Initialize scraper
    for website in config['websites']:
        if website['name'] == 'OshkoshEvents':
            scraper = OshkoshScraper(website)
        elif website['name'] == 'WinnebagoEvents':
            scraper = WinnebagoScraper(website)
        
        # Scrape events
        events = scraper.scrape()
        processed_events = scraper.process_data(events)
        print(f"Dry run for {website['name']}:")
        for event in processed_events:
            print(event)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bluesky Event Publisher')
    parser.add_argument('--dry-run', action='store_true', help='Run the scrapers in dry-run mode')
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        main()