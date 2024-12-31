from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    location = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    region = Column(String, nullable=True)
    published = Column(Boolean, default=False)
    account_username = Column(String, nullable=False)
    config_name = Column(String, nullable=False)
    hashtags = Column(String, nullable=False)

class PublicationSchedule(Base):
    __tablename__ = 'publication_schedule'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    account_username = Column(String, nullable=False)  # To support multiple Bluesky accounts
    is_executed = Column(Boolean, default=False)