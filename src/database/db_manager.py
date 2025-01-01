from datetime import datetime, timedelta
import sqlite3
import os

def connect_to_db(db_path):
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    connection = sqlite3.connect(db_path)
    return connection

def create_event_table(connection):
    cursor = connection.cursor()
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

def add_event(connection, title, start_date, end_date, url, description, location, address, city, region, account_username, config_name, hashtags):
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO events (title, start_date, end_date, url, description, location, address, city, region, published, account_username, config_name, hashtags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, start_date.isoformat(), end_date.isoformat(), url, description, location, address, city, region, False, account_username, config_name, ','.join(hashtags)))
        connection.commit()
    except sqlite3.IntegrityError:
        print(f"Event '{title}' already exists in the database.")

def get_events(connection):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM events')
    return cursor.fetchall()

def update_event_status(connection, event_id, published):
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE events
        SET published = ?
        WHERE id = ?
    ''', (published, event_id))
    connection.commit()

def get_event_by_id(connection, event_id):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    return cursor.fetchone()

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
    for timing in post_timings:
        cursor.execute('''
            INSERT INTO publication_schedule (event_id, scheduled_time, account_username, is_executed)
            VALUES (?, ?, ?, ?)
        ''', (event_id, timing.isoformat(), account_username, False))
    connection.commit()

def get_due_posts(connection):
    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM publication_schedule
        WHERE scheduled_time <= ? AND is_executed = ?
    ''', (datetime.now().isoformat(), False))
    return cursor.fetchall()

def mark_post_as_executed(connection, schedule_id):
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE publication_schedule
        SET is_executed = ?
        WHERE id = ?
    ''', (True, schedule_id))
    connection.commit()