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