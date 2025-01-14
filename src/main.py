import os
import logging
import json
import argparse
from datetime import datetime
from src.config.config_loader import load_config, load_credentials
from src.scrapers.oshkosh_scraper import OshkoshScraper
from src.scrapers.winnebago_scraper import WinnebagoScraper
from src.database.db_manager import (
    connect_to_db, create_event_table, add_event, check_event_exists, get_postable_events, get_events
)
from src.bluesky.auth import authenticate
from src.bluesky.poster import post_event_to_bluesky

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluesky-event-sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_date_string(date_str):
    """Convert date string to ISO format"""
    logger.debug(f"Parsing date string: {date_str}")
    if isinstance(date_str, datetime):
        logger.debug(f"Date string is already a datetime object: {date_str}")
        return date_str
    try:
        # Parse the date string in the format "Friday, January 3, 2025 7:00 PM"
        dt = datetime.strptime(date_str, "%A, %B %d, %Y %I:%M %p")
        logger.debug(f"Successfully parsed date: {dt}")
        return dt
    except ValueError:
        try:
            # Try alternate format "January 3, 2025" if time is not included
            dt = datetime.strptime(date_str, "%B %d, %Y")
            logger.debug(f"Successfully parsed date (no time): {dt}")
            return dt
        except ValueError:
            logger.error(f"Failed to parse date string: {date_str}")
            raise

def dry_run():
    """Run in dry-run mode with detailed summary statistics"""
    logger.info("Starting dry-run mode")
    
    # Statistics tracking
    stats = {
        'websites': {},
        'accounts': {}
    }

    # Load configuration
    config = load_config('config/config.json')
    connection = connect_to_db('database/events.db')

    all_events = []

    # Initialize scraper and process each website
    for website in config['websites']:
        website_stats = {
            'total_scraped': 0,
            'new_events': 0,
            'existing_events': 0,
            'events': []
        }
        
        if website['name'] == 'OshkoshEvents':
            scraper = OshkoshScraper(website)
        elif website['name'] == 'WinnebagoEvents':
            scraper = WinnebagoScraper(website)
        
        # Scrape events
        logger.info(f"Scraping {website['name']}")
        events = scraper.scrape()
        website_stats['total_scraped'] = len(events)
        
        # Process each event
        for event in events:
            logger.info(f"Processing event: {event}")
            try:
                start_date = parse_date_string(event['start_date'])
                end_date = parse_date_string(event['end_date']) if event['end_date'] != 'N/A' else start_date
                
                # Check if event exists
                existing_id = check_event_exists(connection, event['title'], start_date, event['url'])
                
                if existing_id:
                    website_stats['existing_events'] += 1
                else:
                    website_stats['new_events'] += 1
                    website_stats['events'].append({
                        'title': event['title'],
                        'date': start_date.strftime('%Y-%m-%d %H:%M'),
                        'url': event['url']
                    })
                    all_events.append({
                        'title': event['title'],
                        'start_date': start_date,
                        'end_date': end_date,
                        'url': event['url'],
                        'description': event['description'],
                        'location': event['location'],
                        'address': event['address'],
                        'city': event['city'],
                        'region': event['region'],
                        'account_username': website['account_username'],
                        'hashtags': website['hashtags']
                    })

                # Track posts by account
                account_username = website['account_username']
                if account_username not in stats['accounts']:
                    stats['accounts'][account_username] = {
                        'total_posts': 0,
                        'upcoming_posts': []
                    }
                
                if not existing_id:
                    stats['accounts'][account_username]['total_posts'] += 1
                    stats['accounts'][account_username]['upcoming_posts'].append({
                        'event': event['title'],
                        'post_time': start_date.strftime('%Y-%m-%d %H:%M')
                    })
            except ValueError as e:
                logger.error(f"Date parsing error for event {event['title']}: {e}")
                continue

        stats['websites'][website['name']] = website_stats

    # Sort all events by start date
    all_events.sort(key=lambda x: x['start_date'])

    # Simulate posting all events in sorted order
    for event in all_events:
        hashtags = event.get('hashtags', [])
        post_content = f"{event['title']} - {event['description']} {' '.join(hashtags)} {event['url']}"
        logger.info(f"Dry run: Would post: {post_content}")

    # Print summary
    print("\n=== DRY RUN SUMMARY ===\n")
    
    print("Website Statistics:")
    print("-----------------")
    for website_name, website_stats in stats['websites'].items():
        print(f"\n{website_name}:")
        print(f"  Total events scraped: {website_stats['total_scraped']}")
        print(f"  New events found: {website_stats['new_events']}")
        print(f"  Existing events: {website_stats['existing_events']}")
        
        if website_stats['new_events'] > 0:
            print("\n  New Events:")
            for event in website_stats['events']:
                print(f"    - {event['title']} ({event['date']})")

    print("\nBluesky Account Post Summary:")
    print("---------------------------")
    for account, account_stats in stats['accounts'].items():
        print(f"\n{account}:")
        print(f"  Total scheduled posts: {account_stats['total_posts']}")
        if account_stats['upcoming_posts']:
            print("\n  Upcoming posts:")
            for post in account_stats['upcoming_posts']:
                print(f"    Event: {post['event']}")
                print(f"    Post time: {post['post_time']}")
                print()


    print("\nDry run complete!")
    return stats

def post():
    logger.info("post: Starting posting process")
    try:
        # Load configuration
        config = load_config('config/config.json')
        credentials = load_credentials()
        
        # Initialize database
        connection = connect_to_db('database/events.db')
        create_event_table(connection)

        # Authenticate with Bluesky
        authenticated_accounts = {}
        for account in credentials['accounts']:
            auth_token = authenticate(account['username'], account['password'])
            authenticated_accounts[account['username']] = {
                'username': account['username'],
                'auth_token': auth_token
            }

        # Dynamically identify and post events
        for website in config['websites']:
            postable = get_postable_events(connection, website)
            for event in postable:
                account = authenticated_accounts.get(event['account_username'])
                if not account:
                    logger.warning(f"No credentials found for account {event['account_username']}")
                    continue

                if os.getenv('PROD') == 'TRUE':
                    post_event_to_bluesky(event, account)
                    # Mark event as published if needed...
                else:
                    logger.info(f"Dry run: Would post {event['title']} to {account['username']}")

    except Exception as e:
        logger.error(f"post: Failed: {e}")
        raise

if __name__ == "__main__":
    if os.getenv('PROD') == 'TRUE':
        post()
    else:
        dry_run()