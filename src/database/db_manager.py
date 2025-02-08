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
        connection.row_factory = sqlite3.Row
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
            hashtags TEXT,  -- New column for hashtags
            published BOOLEAN NOT NULL,
            account_username TEXT NOT NULL,
            config_name TEXT NOT NULL,
            last_posted TEXT,  -- New column to track last posted timestamp
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
            interval TEXT NOT NULL,
            is_posted BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY(event_id) REFERENCES events(id)
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
def add_event(connection, title, start_date, end_date, url, description, location, address, city, region, hashtags, account_username, config_name):
    cursor = connection.cursor()
    try:
        # First check if event already exists
        existing_event_id = check_event_exists(connection, title, start_date, url)
        if existing_event_id:
            logger.info(f"Event already exists with ID {existing_event_id}: {title}")
            return existing_event_id

        logger.info(f"Adding new event: {title}")
        logger.debug(f"Event hashtags: {hashtags}")
        cursor.execute('''
            INSERT INTO events (
                title, start_date, end_date, url, description, 
                location, address, city, region, hashtags, published, 
                account_username, config_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, start_date.isoformat(), end_date.isoformat(), 
            url, description, location, address, city, region, hashtags,
            False, account_username, config_name
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

def get_event_by_id(connection, event_id):
    """Get event by ID and return as dictionary"""
    cursor = connection.cursor()
    logger.info(f"Fetching event with ID: {event_id}")
    
    # Get column names from the events table
    cursor.execute('PRAGMA table_info(events)')
    columns = [column[1] for column in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    row = cursor.fetchone()
    
    if (row):
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

def mark_post_as_executed(connection, schedule_id):
    cursor = connection.cursor()
    logger.info(f"Marking post as executed for schedule_id: {schedule_id}")
    cursor.execute('''
        UPDATE publication_schedule
        SET is_posted = ?
        WHERE id = ?
    ''', (True, schedule_id))
    connection.commit()

def get_postable_events(connection, website_config):
    """
    Dynamically identify events that should be posted based on their start date
    and configured intervals. Past events are removed from the database.
    """
    logger.info(f"Checking for events to post for {website_config['name']}")
    cursor = connection.cursor()

    interval_map = {
        "30 days": timedelta(days=30),
        "2 weeks": timedelta(days=14),
        "5 days": timedelta(days=5),
        "1 day": timedelta(days=1)
    }

    now = datetime.now()
    events_to_post = []

    # Determine the maximum interval for this website
    intervals = [interval_map[i] for i in website_config["update_intervals"] if i in interval_map]
    if not intervals:
        logger.warning(f"No valid intervals found for {website_config['name']}")
        return []

    max_interval = max(intervals)

    cursor.execute('''
        SELECT id, title, start_date, end_date, url, description, location, 
               address, city, region, hashtags, published, account_username, config_name, last_posted
        FROM events
        WHERE account_username = ?
    ''', (website_config['account_username'],))

    for row in cursor.fetchall():
        event = dict(row)
        event_start = datetime.fromisoformat(event['start_date'])
        time_until_event = event_start - now

        if time_until_event < -timedelta(hours=24):
            logger.info(
                f"Event evaluated: '{event['title']}' is older than 24 hours (start: {event_start}). Removing event from the database."
            )
            cursor.execute("DELETE FROM events WHERE id = ?", (event['id'],))
            connection.commit()
            continue

        # Compute thresholds status for each configured update interval
        last_posted = event['last_posted']
        last_posted_dt = datetime.fromisoformat(last_posted) if last_posted else None
        thresholds_status = {}
        next_post_time = None
        min_delta = None
        for interval_str in website_config['update_intervals']:
            delta = interval_map.get(interval_str)
            scheduled_time = event_start - delta
            status = "Posted" if last_posted_dt and (last_posted_dt >= scheduled_time) else "Pending"
            thresholds_status[interval_str] = status

            if scheduled_time > now and status == "Pending":
                diff = scheduled_time - now
                if min_delta is None or diff < min_delta:
                    min_delta = diff
                    next_post_time = scheduled_time

        # Log evaluation details for every event
        logger.info(
            f"Event: '{event['title']}', Event date: {event_start}, "
            f"Time until next post: {min_delta if next_post_time else 'N/A'}, "
            f"Configured update intervals: {website_config['update_intervals']}, "
            f"Thresholds status: {thresholds_status}"
        )

        if time_until_event > max_interval:
            logger.info(
                f"Event evaluated: '{event['title']}' is not yet eligible. "
                f"Time until event: {time_until_event} exceeds max interval: {max_interval}"
            )
            continue

        if last_posted:
            eligible = False
            for interval_str in website_config['update_intervals']:
                delta = interval_map.get(interval_str)
                scheduled_time = event_start - delta
                # Only allow a new post if the last post was before this interval's threshold
                if now >= scheduled_time and (now - last_posted_dt) > delta:
                    eligible = True
                    break

            if not eligible:
                logger.info(
                    f"Event evaluated: '{event['title']}' was already posted at {last_posted_dt} "
                    f"and does not qualify for any interval."
                )
                continue

        # Evaluate against each configured threshold; if any qualifies, add event to post
        qualified = False
        for interval_str in website_config['update_intervals']:
            delta = interval_map.get(interval_str)
            if delta and time_until_event <= delta:
                next_post_for_interval = event_start - delta
                logger.info(
                    f"Event evaluated: '{event['title']}'. Last posted: "
                    f"{last_posted if last_posted else 'Never'}, "
                    f"Next post scheduled for: {next_post_for_interval} "
                    f"(meets threshold: {interval_str})"
                )
                events_to_post.append(event)
                qualified = True
                break
        if not qualified:
            logger.info(
                f"Event evaluated: '{event['title']}' does not meet any posting threshold. "
                f"Time until event: {time_until_event}"
            )

    logger.info(f"Found {len(events_to_post)} events to post for {website_config['name']}")
    return events_to_post

def schedule_event_posts(connection, event_id, event_start_date, intervals):
    cursor = connection.cursor()
    for interval in intervals:
        scheduled_time = event_start_date - interval
        cursor.execute('''
            INSERT INTO publication_schedule (event_id, scheduled_time, interval, is_posted)
            VALUES (?, ?, ?, ?)
        ''', (event_id, scheduled_time.isoformat(), str(interval), False))
    connection.commit()