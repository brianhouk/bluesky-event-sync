import logging
import sqlite3
import os
from datetime import datetime, timedelta

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

def connect_to_db(db_path):
    logger.info(f"connect_to_db: Connecting to {db_path}")
    try:
        if not os.path.exists(os.path.dirname(db_path)):
            logger.info(f"Creating database directory: {os.path.dirname(db_path)}")
            os.makedirs(os.path.dirname(db_path))
        logger.info(f"Connecting to database: {db_path}")
        connection = sqlite3.connect(db_path)
        return connection
    except Exception as e:
        logger.error(f"connect_to_db: Failed: {e}")
        raise

def create_event_table(connection):
    cursor = connection.cursor()
    logger.info("Creating events table if not exists")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            location TEXT,
            address TEXT,
            city TEXT,
            region TEXT,
            published BOOLEAN NOT NULL,
            account_username TEXT NOT NULL,
            config_name TEXT NOT NULL,
            hashtags TEXT NOT NULL,
            UNIQUE(title, start_date, url)
        )
    ''')
    connection.commit()

def create_publication_schedule_table(connection):
    cursor = connection.cursor()
    logger.info("Creating publication_schedule table if not exists")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publication_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            scheduled_time TEXT NOT NULL,
            account_username TEXT NOT NULL,
            is_executed BOOLEAN NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    ''')
    connection.commit()

def check_event_exists(connection, title, start_date, url):
    """Check if an event already exists in the database"""
    cursor = connection.cursor()
    logger.info(f"Checking for existing event: {title} on {start_date}")
    cursor.execute('''
        SELECT id FROM events 
        WHERE title = ? AND start_date = ? AND url = ?
    ''', (title, start_date.isoformat(), url))
    result = cursor.fetchone()
    return result[0] if result else None

def add_event(connection, title, start_date, end_date, url, description, location, address, city, region, account_username, config_name, hashtags):
    cursor = connection.cursor()
    try:
        # First check if event already exists
        existing_event_id = check_event_exists(connection, title, start_date, url)
        if existing_event_id:
            logger.info(f"Event already exists with ID {existing_event_id}: {title}")
            return existing_event_id

        logger.info(f"Adding new event: {title}")
        cursor.execute('''
            INSERT INTO events (
                title, start_date, end_date, url, description, 
                location, address, city, region, published, 
                account_username, config_name, hashtags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, start_date.isoformat(), end_date.isoformat(), 
            url, description, location, address, city, region, 
            False, account_username, config_name, ','.join(hashtags)
        ))
        connection.commit()
        event_id = cursor.lastrowid
        logger.info(f"Event added with ID: {event_id}")
        return event_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Database integrity error for event '{title}': {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to add event '{title}': {e}")
        return None

def get_events(connection):
    cursor = connection.cursor()
    logger.info("Fetching all events")
    cursor.execute('SELECT * FROM events')
    return cursor.fetchall()

def update_event_status(connection, event_id, published):
    cursor = connection.cursor()
    logger.info(f"Updating event status for event_id: {event_id} to published: {published}")
    cursor.execute('''
        UPDATE events
        SET published = ?
        WHERE id = ?
    ''', (published, event_id))
    connection.commit()

def get_event_by_id(connection, event_id):
    """Get event by ID and return as dictionary"""
    cursor = connection.cursor()
    logger.info(f"Fetching event with ID: {event_id}")
    
    # Get column names from the events table
    cursor.execute('PRAGMA table_info(events)')
    columns = [column[1] for column in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    row = cursor.fetchone()
    
    if row:
        # Convert tuple to dictionary with column names
        event_dict = dict(zip(columns, row))
        logger.info(f"Found event: {event_dict['title']}")
        return event_dict
    
    logger.warning(f"No event found with ID: {event_id}")
    return None

def calculate_post_timings(event_date):
    intervals = [
        timedelta(weeks=4),
        timedelta(weeks=2),
        timedelta(weeks=1),
        timedelta(days=5),
        timedelta(days=1),
        timedelta(hours=2)
    ]
    return [event_date - interval for interval in intervals]

def store_post_timings(connection, event_id, post_timings, account_username):
    cursor = connection.cursor()
    logger.info(f"Storing post timings for event_id: {event_id}")
    for timing in post_timings:
        cursor.execute('''
            INSERT INTO publication_schedule (event_id, scheduled_time, account_username, is_executed)
            VALUES (?, ?, ?, ?)
        ''', (event_id, timing.isoformat(), account_username, False))
    connection.commit()

def get_due_posts(connection):
    """Fetch all due posts and return them as dictionaries"""
    cursor = connection.cursor()
    logger.info("Fetching due posts")
    
    # Get column names from the publication_schedule table
    cursor.execute('PRAGMA table_info(publication_schedule)')
    columns = [column[1] for column in cursor.fetchall()]
    
    cursor.execute('''
        SELECT * FROM publication_schedule
        WHERE scheduled_time <= ? AND is_executed = ?
    ''', (datetime.now().isoformat(), False))
    
    # Convert tuples to dictionaries with column names
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    logger.info(f"Found {len(results)} due posts")
    return results

def mark_post_as_executed(connection, schedule_id):
    cursor = connection.cursor()
    logger.info(f"Marking post as executed for schedule_id: {schedule_id}")
    cursor.execute('''
        UPDATE publication_schedule
        SET is_executed = ?
        WHERE id = ?
    ''', (True, schedule_id))
    connection.commit()