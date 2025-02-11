import os
import logging
import sqlite3
from datetime import datetime, timedelta
from src.database.db_manager import connect_to_db, create_event_table, create_publication_schedule_table, add_event, schedule_event_posts

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

def post_wall_message(message, account_username, config_name, db_path):
    connection = connect_to_db(db_path)
    create_event_table(connection)
    create_publication_schedule_table(connection)

    now = datetime.now()
    event_id = add_event(
        connection,
        title="Wall Message",
        start_date=now,
        end_date=now,
        url="",
        description=message,
        location="",
        address="",
        city="",
        region="",
        hashtags="",
        account_username=account_username,
        config_name=config_name
    )

    if event_id:
        schedule_event_posts(connection, event_id, now, [timedelta(seconds=0)])
        logger.info(f"Wall message scheduled for immediate posting: {message}")
    else:
        logger.error("Failed to schedule wall message")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Post a wall message to Bluesky")
    parser.add_argument("message", help="The message to post")
    parser.add_argument("account_username", help="The Bluesky account username")
    parser.add_argument("config_name", help="The configuration name")
    parser.add_argument("--db-path", type=str, default="database/events.db", help="Path to the database file")

    args = parser.parse_args()

    post_wall_message(args.message, args.account_username, args.config_name, args.db_path)