import os
import logging
import json
import argparse
from datetime import datetime, timedelta
from src.config.config_loader import load_config, load_credentials
from src.scrapers.oshkosh_scraper import OshkoshScraper
from src.scrapers.winnebago_scraper import WinnebagoScraper
from src.database.db_manager import (
    connect_to_db, create_event_table, create_publication_schedule_table, add_event, check_event_exists, get_postable_events, get_events, schedule_event_posts
)
from src.bluesky.auth import authenticate
from src.bluesky.poster import post_event_to_bluesky

# Import the backup script
from src.scripts.backup_database import create_backup, cleanup_old_backups

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
            try:
                # Try ISO format "2025-01-20T08:00:00"
                dt = datetime.fromisoformat(date_str)
                logger.debug(f"Successfully parsed ISO date: {dt}")
                return dt
            except ValueError:
                logger.error(f"Failed to parse date string: {date_str}")
                raise

def dry_run(skip_scraping):
    logger.info("Starting dry-run mode")

    config = load_config('config/config.json')
    connection = connect_to_db('database/events.db')
    create_event_table(connection)
    create_publication_schedule_table(connection)

    if not skip_scraping:
        for website in config['websites']:
            if website['name'] == 'OshkoshEvents':
                scraper = OshkoshScraper(website)
            elif website['name'] == 'WinnebagoEvents':
                scraper = WinnebagoScraper(website)
            events = scraper.scrape()
            for ev in events:
                try:
                    start_date = parse_date_string(ev['start_date'])
                    end_date = parse_date_string(ev['end_date']) if ev['end_date'] != 'N/A' else start_date
                    if not check_event_exists(connection, ev['title'], start_date, ev['url']):
                        event_id = add_event(
                            connection,
                            ev['title'],
                            start_date,
                            end_date,
                            ev['url'],
                            ev.get('description', ''),
                            ev.get('location', ''),
                            ev.get('address', ''),
                            ev.get('city', ''),
                            ev.get('region', ''),
                            ' '.join(website.get('hashtags', [])),  # Add hashtags from config
                            website['account_username'],
                            website['name']
                        )
                        if event_id:
                            intervals = [timedelta(days=30), timedelta(days=14), timedelta(days=5), timedelta(days=1)]
                            schedule_event_posts(connection, event_id, start_date, intervals)
                except ValueError as e:
                    logger.error(f"Date parsing error: {e}")
                    continue

    all_events = []
    for website in config['websites']:
        postable_events = get_postable_events(connection, website)
        all_events.extend(postable_events)

    all_events.sort(key=lambda x: parse_date_string(x['start_date']))
    for event in all_events:
        start_date = parse_date_string(event['start_date'])
        hashtags = event.get('hashtags', '').split()  # Retrieve hashtags from the database
        post_content = f"{event['title']} ({start_date.strftime('%Y-%m-%d %H:%M')}) - {event['description']} {' '.join(hashtags)} {event['url']}"

        logger.info(f"Dry run: Would post: {post_content}")
    return True

def post(skip_scraping):
    logger.info("post: Starting production mode")
    try:
        config = load_config('config/config.json')
        credentials = load_credentials()
        connection = connect_to_db('database/events.db')
        create_event_table(connection)
        create_publication_schedule_table(connection)

        # Create a backup before modifying the database
        create_backup()
        cleanup_old_backups()

        max_posts = int(os.getenv('MAX_POSTS', '0'))
        post_count = 0

        if not skip_scraping:
            for website in config['websites']:
                if website['name'] == 'OshkoshEvents':
                    scraper = OshkoshScraper(website)
                elif website['name'] == 'WinnebagoEvents':
                    scraper = WinnebagoScraper(website)
                events = scraper.scrape()
                for ev in events:
                    try:
                        start_date = parse_date_string(ev['start_date'])
                        end_date = parse_date_string(ev['end_date']) if ev['end_date'] != 'N/A' else start_date
                        if not check_event_exists(connection, ev['title'], start_date, ev['url']):
                            event_id = add_event(
                                connection,
                                ev['title'],
                                start_date,
                                end_date,
                                ev['url'],
                                ev.get('description', ''),
                                ev.get('location', ''),
                                ev.get('address', ''),
                                ev.get('city', ''),
                                ev.get('region', ''),
                                ev.get('hashtags', ''),  # Add hashtags from event data
                                website['account_username'],
                                website['name']
                            )
                            if event_id:
                                intervals = [timedelta(days=30), timedelta(days=14), timedelta(days=5), timedelta(days=1)]
                                schedule_event_posts(connection, event_id, start_date, intervals)
                    except ValueError as e:
                        logger.error(f"Date parsing error: {e}")
                        continue

        authenticated_accounts = {}
        for account in credentials['accounts']:
            token = authenticate(account['username'], account['password'])
            authenticated_accounts[account['username']] = {
                'username': account['username'],
                'password': account['password'],  # Ensure password is included
                'auth_token': token
            }

        all_events = []
        for website in config['websites']:
            postable_events = get_postable_events(connection, website)
            all_events.extend(postable_events)

        all_events.sort(key=lambda x: parse_date_string(x['start_date']))
        for event in all_events:
            if max_posts > 0 and post_count >= max_posts:
                logger.info(f"Reached the maximum number of posts: {max_posts}")
                break

            account = authenticated_accounts.get(event['account_username'])
            if not account:
                logger.warning(f"No credentials for account {event['account_username']}")
                continue
            start_date = parse_date_string(event['start_date'])
            hashtags = event.get('hashtags', '').split()  # Retrieve hashtags from the database
            post_content = f"{event['title']} ({start_date.strftime('%Y-%m-%d %H:%M')}) - {event['description']} {' '.join(hashtags)} {event['url']}"

            try:
                if os.getenv('PROD') == 'TRUE':
                    post_event_to_bluesky(event, account, connection)
                    post_count += 1
                else:
                    logger.info(f"Dry run: Would post {post_content} to {account['username']}")
            except ValueError as e:
                logger.error(f"Failed to post event: {event['title']} due to: {e}")
                continue

    except Exception as e:
        logger.error(f"post: Failed: {e}")
        raise

if __name__ == "__main__":
    skip_scraping = os.getenv('SKIP_SCRAPING', 'FALSE').upper() == 'TRUE'

    if os.getenv('PROD') == 'TRUE':
        post(skip_scraping)
    else:
        dry_run(skip_scraping)