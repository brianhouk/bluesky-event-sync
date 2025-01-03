import logging
from typing import Optional
from atproto_client import Client, Session, SessionEvent

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

def get_session() -> Optional[str]:
    """Retrieve saved session from file if it exists"""
    try:
        with open('session.txt', encoding='UTF-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def save_session(session_string: str) -> None:
    """Save session string to file"""
    with open('session.txt', 'w', encoding='UTF-8') as f:
        f.write(session_string)

def on_session_change(event: SessionEvent, session: Session) -> None:
    """Handle session change events"""
    logger.info(f'Session changed: {event}, {session.handle}')
    if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
        logger.info('Saving changed session')
        save_session(session.export())

def authenticate(username: str, password: str) -> Client:
    """
    Authenticate with Bluesky using session reuse if available
    
    Args:
        username: Bluesky username
        password: Bluesky password from environment variable
    
    Returns:
        Client: Authenticated Bluesky client
    """
    client = Client()
    client.on_session_change(on_session_change)

    session_string = get_session()
    if session_string:
        logger.info('Reusing existing session')
        try:
            client.login(session_string=session_string)
        except Exception as e:
            logger.info(f'Session reuse failed: {e}. Creating new session.')
            client.login(username, password)
    else:
        logger.info('Creating new session')
        client.login(username, password)

    return client