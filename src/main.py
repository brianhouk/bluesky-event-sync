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

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load configuration
    logger.debug("Loading configuration")
    config = load_config('config/config.json')
    logger.debug(f"Configuration loaded: {config}")
    
    logger.debug("Loading credentials")
    credentials = load_credentials(config)
    logger.debug(f"Credentials loaded: {credentials}")
    
    # Initialize database
    logger.debug("Connecting to database")
    connection = connect_to_db('database/events.db')
    logger.debug("Creating event table")
    create_event_table(connection)
    logger.debug("Creating publication schedule table")
    create_publication_schedule_table(connection)

    # Authenticate with Bluesky
    for account in credentials['accounts']:
        try:
            logger.debug(f"Authenticating account: {account['username']}")
            auth_token = authenticate(account['username'], account['password'])
            account['auth_token'] = auth_token
            logger.debug(f"Authentication token for {account['username']}: {auth_token}")
        except Exception as e:
            logger.error(f"Authentication failed for user {account['username']}: {e}")
            continue

    # Initialize scraper
    for website in config['websites']:
        account_username = website['account_username']
        logger.debug(f"Processing website: {website['name']} with account: {account_username}")
        account = next((acc for acc in credentials['accounts'] if acc['username'] == account_username), None)
        if not account or 'auth_token' not in account:
            logger.warning(f"Skipping website {website['name']} due to missing or failed authentication for account {account_username}")
            continue

        if website['name'] == 'OshkoshEvents':
            scraper = OshkoshScraper(website)
        elif website['name'] == 'WinnebagoEvents':
            scraper = WinnebagoScraper(website)
        
        # Scrape events
        logger.debug(f"Scraping events for website: {website['name']}")
        events = scraper.scrape()
        logger.debug(f"Events scraped: {events}")
        for event in events:
            logger.debug(f"Adding event: {event['title']}")
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
            logger.debug(f"Event added with ID: {event_id}")
            post_timings = calculate_post_timings(datetime.fromisoformat(event['start_date']))
            logger.debug(f"Post timings calculated: {post_timings}")
            store_post_timings(connection, event_id, post_timings, account_username)
            logger.debug(f"Post timings stored for event ID: {event_id}")

    # Check for due posts
    logger.debug("Checking for due posts")
    due_posts = get_due_posts(connection)
    logger.debug(f"Due posts: {due_posts}")
    for post in due_posts:
        event = get_event_by_id(connection, post['event_id'])
        logger.debug(f"Processing due post for event: {event['title']}")
        account = next((acc for acc in credentials['accounts'] if acc['username'] == post['account_username']), None)
        if not account or 'auth_token' not in account:
            logger.warning(f"Skipping post for event {event['title']} due to missing or failed authentication for account {post['account_username']}")
            continue

        if os.getenv('PROD'):
            logger.debug(f"Posting event to Bluesky: {event['title']}")
            post_event_to_bluesky(event, account)
        else:
            logger.debug(f"Dry run for event: {event['title']}")
            dry_run(event)
        mark_post_as_executed(connection, post['id'])
        logger.debug(f"Marked post as executed for event ID: {post['event_id']}")

def dry_run():
    # Load configuration
    logger.debug("Loading configuration for dry run")
    config = load_config('config/config.json')

    # Initialize scraper
    for website in config['websites']:
        logger.debug(f"Dry run for website: {website['name']}")
        if website['name'] == 'OshkoshEvents':
            scraper = OshkoshScraper(website)
        elif website['name'] == 'WinnebagoEvents':
            scraper = WinnebagoScraper(website)
        
        # Scrape events
        events = scraper.scrape()
        processed_events = scraper.process_data(events)
        logger.debug(f"Dry run events processed for {website['name']}: {processed_events}")
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