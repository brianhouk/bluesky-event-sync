import pytest
import sqlite3
from datetime import datetime, timedelta
from src.database.db_manager import connect_to_db, create_event_table, create_publication_schedule_table, add_event, get_postable_events

@pytest.fixture(scope="module")
def connection():
    # Create an in-memory SQLite database
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_event_table(connection)
    create_publication_schedule_table(connection)
    yield connection
    connection.close()

def test_get_postable_events_no_events(connection):
    website_config = {
        "name": "TestSite",
        "account_username": "testuser.bsky.social",
        "update_intervals": ["30 days", "2 weeks", "5 days", "1 day"]
    }
    events = get_postable_events(connection, website_config)
    assert len(events) == 0

def test_get_postable_events_with_events(connection):
    website_config = {
        "name": "TestSite",
        "account_username": "testuser.bsky.social",
        "update_intervals": ["30 days", "2 weeks", "5 days", "1 day"]
    }
    
    # Add events to the database
    now = datetime.now()
    event1_id = add_event(
        connection, "Event 1", now + timedelta(days=40), now + timedelta(days=41),
        "http://example.com/event1", "Description 1", "Location 1", "Address 1", "City 1", "Region 1",
        "hashtag1", "testuser.bsky.social", "TestConfig"
    )
    event2_id = add_event(
        connection, "Event 2", now + timedelta(days=10), now + timedelta(days=11),
        "http://example.com/event2", "Description 2", "Location 2", "Address 2", "City 2", "Region 2",
        "hashtag2", "testuser.bsky.social", "TestConfig"
    )
    event3_id = add_event(
        connection, "Event 3", now + timedelta(days=1), now + timedelta(days=2),
        "http://example.com/event3", "Description 3", "Location 3", "Address 3", "City 3", "Region 3",
        "hashtag3", "testuser.bsky.social", "TestConfig"
    )
    
    events = get_postable_events(connection, website_config)
    assert len(events) == 2
    assert any(event['title'] == "Event 2" for event in events)
    assert any(event['title'] == "Event 3" for event in events)

def test_get_postable_events_past_event(connection):
    website_config = {
        "name": "TestSite",
        "account_username": "testuser.bsky.social",
        "update_intervals": ["30 days", "2 weeks", "5 days", "1 day"]
    }
    
    # Add a past event to the database
    now = datetime.now()
    event_id = add_event(
        connection, "Past Event", now - timedelta(days=10), now - timedelta(days=9),
        "http://example.com/past_event", "Description Past", "Location Past", "Address Past", "City Past", "Region Past",
        "hashtag_past", "testuser.bsky.social", "TestConfig"
    )
    
    events = get_postable_events(connection, website_config)
    assert len(events) == 2  # Should still be 2 from the previous test, past event should be removed

def test_get_postable_events_no_valid_intervals(connection):
    website_config = {
        "name": "TestSite",
        "account_username": "testuser.bsky.social",
        "update_intervals": ["invalid_interval"]
    }
    
    events = get_postable_events(connection, website_config)
    assert len(events) == 0  # No valid intervals, so no events should be returned

def test_get_postable_events_event_already_posted(connection):
    website_config = {
        "name": "TestSite",
        "account_username": "testuser.bsky.social",
        "update_intervals": ["30 days", "2 weeks", "5 days", "1 day"]
    }
    
    # Add an event that has already been posted
    now = datetime.now()
    event_id = add_event(
        connection, "Posted Event", now + timedelta(days=10), now + timedelta(days=11),
        "http://example.com/posted_event", "Description Posted", "Location Posted", "Address Posted", "City Posted", "Region Posted",
        "hashtag_posted", "testuser.bsky.social", "TestConfig"
    )
    
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE events
        SET last_posted = ?
        WHERE id = ?
    ''', ((now - timedelta(days=1)).isoformat(), event_id))
    connection.commit()
    
    events = get_postable_events(connection, website_config)
    assert len(events) == 2  # Should still be 2 from the previous test, posted event should not be included