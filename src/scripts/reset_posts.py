import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.database.db_manager import connect_to_db, get_postable_events
from src.config.config_loader import load_config

def parse_args():
    parser = argparse.ArgumentParser(description='Reset post status for specific events')
    parser.add_argument(
        '--db-path',
        default=os.path.join(project_root, 'database', 'events.db'),
        help='Path to the SQLite database file'
    )
    return parser.parse_args()

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

def reset_post_status(db_path):
    """Reset the post status for events that didn't post correctly"""
    try:
        connection = connect_to_db(db_path)
        cursor = connection.cursor()
        
        reset_query = """
            UPDATE events 
            SET last_posted = NULL
            WHERE DATE(start_date) = '2025-02-15' 
            AND title IN (
                'Grand Opening Celebration of X-Golf Oshkosh',
                'Oshkosh Farmers Market',
                'Sweethearts and Sweetarts Valentines Family Event 2025', 
                'Oshkosh Public Museum Auxiliary, Inc. Celebrates 100 Years!',
                'Free Cooking Class with Jeremiah McDuffie',
                'Sturgeon Spirits 2nd Anniversary Party!',
                'Downtown Oshkosh Chocolate Stroll',
                'Spaghetti Dinner',
                '2nd Anniversary Celebration',
                'Northeast Wisconsin 2025 Chinese New Year Celebration',
                'Live Music featuring Whitney Rose'
            )
        """
        
        cursor.execute(reset_query)
        rows_affected = cursor.rowcount
        connection.commit()
        logger.info(f"Reset post status for {rows_affected} events")
        
        # Verification steps
        logger.info("\nVerification Results:")
        logger.info("====================")
        
        cursor.execute("""
            SELECT title, start_date, last_posted
            FROM events
            WHERE DATE(start_date) = '2025-02-15'
            AND last_posted IS NULL
        """)
        reset_events = cursor.fetchall()
        
        logger.info(f"Found {len(reset_events)} reset events:")
        for event in reset_events:
            logger.info(f"\nTitle: {event['title']}")
            logger.info(f"Start Date: {event['start_date']}")
            logger.info(f"Last Posted: {event['last_posted']}")
        
        # Preview next posts
        config = load_config(os.path.join(project_root, 'config', 'config.json'))
        logger.info("\nNext Posts Preview:")
        logger.info("==================")
        
        for website in config['websites']:
            postable_events = get_postable_events(connection, website)
            logger.info(f"\nWebsite: {website['name']}")
            logger.info(f"Found {len(postable_events)} events to post:")
            
            for event in postable_events:
                logger.info(f"\nTitle: {event['title']}")
                logger.info(f"Start: {event['start_date']}")
                logger.info(f"URL: {event['url']}")
        
        return rows_affected
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    try:
        args = parse_args()
        logger.info("Starting post status reset and verification...")
        logger.info(f"Using database: {args.db_path}")
        num_reset = reset_post_status(args.db_path)
        logger.info(f"Process complete. Reset {num_reset} events.")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)
