from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    is_posted = Column(Boolean, default=False)

class PublicationSchedule(Base):
    __tablename__ = 'publication_schedule'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    account_id = Column(String, nullable=False)  # To support multiple Bluesky accounts
    is_executed = Column(Boolean, default=False)