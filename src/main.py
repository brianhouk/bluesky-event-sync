import json
from src.config.config_loader import load_config
from src.scrapers.oshkosh_scraper import OshkoshScraper
from src.database.db_manager import DatabaseManager
from src.bluesky.auth import authenticate
from src.bluesky.poster import post_event

def main():
    # Load configuration
    config = load_config('config/config.json')
    
    # Initialize database
    db_manager = DatabaseManager('database/events.db')
    db_manager.create_tables()

    # Authenticate with Bluesky
    auth_token = authenticate('config/credentials.json')

    # Initialize scraper
    oshkosh_scraper = OshkoshScraper(config['websites']['oshkosh'])
    
    # Scrape events
    events = oshkosh_scraper.scrape_events()
    
    # Post events to Bluesky
    for event in events:
        post_event(auth_token, event)

if __name__ == "__main__":
    main()