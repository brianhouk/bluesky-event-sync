import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, Event, PublicationSchedule

# Fixture to create an in-memory SQLite database and initialize tables.
@pytest.fixture(scope="module")
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine

# Fixture to provide a session per test and roll back changes after test completion.
@pytest.fixture(scope="function")
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()

def test_create_event(session):
    # Create an Event instance using datetime objects.
    event = Event(
        title="Test Event",
        start_date=datetime.strptime("2023-01-01 10:00:00", "%Y-%m-%d %H:%M:%S"),
        end_date=datetime.strptime("2023-01-01 11:00:00", "%Y-%m-%d %H:%M:%S"),
        url="http://example.com/event",
        description="This is a test event.",
        location="Test Location",
        address="123 Test Ave",
        city="Test City",
        region="TS",
        published=False,
        account_username="user@example.com",
        config_name="TestConfig"
    )
    session.add(event)
    session.commit()

    # Query the event and validate the field values.
    result = session.query(Event).filter_by(title="Test Event").first()
    assert result is not None
    assert result.title == "Test Event"
    assert result.start_date == datetime.strptime("2023-01-01 10:00:00", "%Y-%m-%d %H:%M:%S")
    assert result.end_date == datetime.strptime("2023-01-01 11:00:00", "%Y-%m-%d %H:%M:%S")
    assert result.url == "http://example.com/event"
    assert result.published is False

def test_event_unique_constraint(session):
    # Create first event with unique key (title, start_date, url).
    event1 = Event(
        title="Unique Event",
        start_date=datetime.strptime("2023-01-02 10:00:00", "%Y-%m-%d %H:%M:%S"),
        end_date=datetime.strptime("2023-01-02 11:00:00", "%Y-%m-%d %H:%M:%S"),
        url="http://unique.com/event",
        description="First instance",
        location="Loc1",
        address="Address1",
        city="City1",
        region="R1",
        published=False,
        account_username="user@example.com",
        config_name="TestConfig"
    )
    session.add(event1)
    session.commit()

    # Create a second event with the same title, start_date and url.
    event2 = Event(
        title="Unique Event",  # Same title
        start_date=datetime.strptime("2023-01-02 10:00:00", "%Y-%m-%d %H:%M:%S"),  # Same start_date
        end_date=datetime.strptime("2023-01-02 12:00:00", "%Y-%m-%d %H:%M:%S"),
        url="http://unique.com/event",  # Same url
        description="Second instance",
        location="Loc2",
        address="Address2",
        city="City2",
        region="R2",
        published=True,
        account_username="another@example.com",
        config_name="AnotherConfig"
    )
    session.add(event2)
    # Committing should raise an IntegrityError because of the unique constraint.
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_publication_schedule(session):
    # Create a PublicationSchedule instance.
    schedule = PublicationSchedule(
        event_id=1,
        scheduled_time=datetime.strptime("2023-01-05 10:00:00", "%Y-%m-%d %H:%M:%S"),
        account_username="user@example.com",
        is_executed=False
    )
    session.add(schedule)
    session.commit()

    # Query the publication schedule and verify values.
    result = session.query(PublicationSchedule).filter_by(event_id=1).first()
    assert result is not None
    assert result.event_id == 1
    assert result.scheduled_time == datetime.strptime("2023-01-05 10:00:00", "%Y-%m-%d %H:%M:%S")
    assert result.account_username == "user@example.com"
    assert result.is_executed is False