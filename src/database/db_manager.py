from datetime import datetime, timedelta

def connect_to_db(db_path):
    import sqlite3
    connection = sqlite3.connect(db_path)
    return connection

def create_event_table(connection):
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            published BOOLEAN NOT NULL,
            next_publish_date TEXT NOT NULL
        )
    ''')
    connection.commit()

def add_event(connection, url, next_publish_date):
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO events (url, published, next_publish_date)
        VALUES (?, ?, ?)
    ''', (url, False, next_publish_date))
    connection.commit()

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

def close_connection(connection):
    connection.close()

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

def store_post_timings(connection, event_id, post_timings, account_id):
    cursor = connection.cursor()
    for timing in post_timings:
        cursor.execute('''
            INSERT INTO publication_schedule (event_id, scheduled_time, account_id, is_executed)
            VALUES (?, ?, ?, ?)
        ''', (event_id, timing, account_id, False))
    connection.commit()

def get_due_posts(connection):
    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM publication_schedule
        WHERE scheduled_time <= ? AND is_executed = ?
    ''', (datetime.now(), False))
    return cursor.fetchall()

def mark_post_as_executed(connection, schedule_id):
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE publication_schedule
        SET is_executed = ?
        WHERE id = ?
    ''', (True, schedule_id))
    connection.commit()