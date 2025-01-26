import os
import logging
from datetime import datetime
from atproto import Client, models, client_utils
from src.database.db_manager import mark_post_as_executed
import json

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

class BlueskySession:
    _instance = None
    
    def __init__(self):
        self.session_file = "bluesky_session.json"
        self.client = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = BlueskySession()
        return cls._instance
    
    def load_session(self):
        """Load existing session if available"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    self.client = Client()
                    # Use the correct session restoration method
                    self.client.restore_auth(
                        refresh_jwt=session_data.get('refreshJwt'),
                        access_jwt=session_data.get('accessJwt'),
                        handle=session_data.get('handle'),
                        did=session_data.get('did')
                    )
                    return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
        return False

    def save_session(self):
        """Save session data to file"""
        try:
            if self.client and hasattr(self.client, 'auth'):
                session_data = {
                    'refreshJwt': self.client.auth.refresh_jwt,
                    'accessJwt': self.client.auth.access_jwt,
                    'handle': self.client.auth.handle,
                    'did': self.client.auth.did
                }
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f)
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def get_client(self, username, password):
        """Get or create authenticated client"""
        try:
            if self.client is None or not self.load_session():
                logger.info(f"Creating new session for {username}")
                self.client = Client()
                self.client.login(username, password)
                self.save_session()
            return self.client
        except Exception as e:
            logger.error(f"Failed to get client: {e}")
            raise

def post_event_to_bluesky(event_data, account_info, connection):
    """
    Posts an event to Bluesky using the provided event data and account information.
    
    Parameters:
        event_data (dict): The data of the event to be posted.
        account_info (dict): The account information for posting to Bluesky.
        connection: Database connection to update the last_posted timestamp.
    
    Returns:
        response (dict): The response from the Bluesky API after posting the event.
    """
    logger.info(f"post_event_to_bluesky: Starting for {account_info['username']}")
    try:
        session = BlueskySession.get_instance()
        client = session.get_client(account_info['username'], account_info['password'])
        logger.info(f"Successfully got client for user {account_info['username']}")

        logger.info(f"Preparing to post event: {event_data['title']}")
        logger.debug(f"Full event data: {event_data}")

        hashtags = event_data.get('hashtags', '').split()
        logger.debug(f"Event hashtags: {hashtags}")
        
        # Ensure start_date is a datetime object
        if isinstance(event_data['start_date'], str):
            logger.debug(f"Parsing start_date from string: {event_data['start_date']}")
            event_data['start_date'] = datetime.fromisoformat(event_data['start_date'])
        
        start_date_str = event_data['start_date'].strftime('%Y-%m-%d %H:%M')
        
        # Build post content with a link
        text_builder = client_utils.TextBuilder()
        text_builder.link(event_data['title'], event_data['url'])
        
        # Calculate remaining characters for description
        base_text = f" ({start_date_str}) "
        hashtag_text = ' '.join(hashtags)
        
        # Calculate max length for description
        title_length = len(event_data['title'])
        url_length = len(event_data['url'])
        base_length = len(base_text)
        hashtag_length = len(hashtag_text)
        
        # URL counts as 23 characters in Bluesky
        url_char_count = 23
        
        # Calculate available space for description
        available_chars = 300 - (title_length + url_char_count + base_length + hashtag_length + 1)  # +1 for space
        
        # Truncate description if needed
        description = event_data['description']
        if available_chars > 0:
            if len(description) > available_chars:
                description = description[:available_chars-3] + "..."
            text_builder.text(f"{base_text}{description} {hashtag_text}")
        else:
            # If no space for description, just post title, date and hashtags
            text_builder.text(f"{base_text}{hashtag_text}")
        
        post_content = text_builder
        logger.info(f"Posting content: {post_content}")
        
        post = client.send_post(text=post_content)
        logger.info(f"Post sent successfully: {post}")
        logger.debug(f"Post URI: {post.uri}, Post CID: {post.cid}")

        # Update the last_posted timestamp
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE events 
            SET last_posted = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), event_data['id']))
        connection.commit()

        # Mark the post as executed in the publication schedule
        if 'schedule_id' in event_data:
            mark_post_as_executed(connection, event_data['schedule_id'])

    except Exception as e:
        logger.error(f"post_event_to_bluesky: Failed: {e}")
        raise

def dry_run(event_data):
    """
    Simulates posting an event without actually sending it to Bluesky.
    
    Parameters:
        event_data (dict): The data of the event to be posted.
    
    Returns:
        None
    """
    logger.info("Performing dry run")
    logger.debug(f"Event data for dry run: {event_data}")
    
    hashtags = event_data.get('hashtags', [])
    
    # Ensure start_date is a datetime object
    if isinstance(event_data['start_date'], str):
        logger.debug(f"Parsing start_date from string: {event_data['start_date']}")
        event_data['start_date'] = datetime.fromisoformat(event_data['start_date'])
    
    start_date_str = event_data['start_date'].strftime('%Y-%m-%d %H:%M')
    logger.debug(f"Formatted start_date_str: {start_date_str}")
    
    post_content = f"{event_data['title']} ({start_date_str}) - {event_data['description']} {' '.join(hashtags)} {event_data['url']}"

    # Check if post_content exceeds 300 characters
    if len(post_content) > 300:
        logger.warning("Post content exceeds 300 characters, removing description")
        post_content = f"{event_data['title']} ({start_date_str}) {' '.join(hashtags)} {event_data['url']}"

    # Ensure post_content is within the limit
    if len(post_content) > 300:
        logger.error("Post content still exceeds 300 characters after removing description")
        raise ValueError("Post content exceeds 300 characters")

    logger.info(f"Dry run - Would post: {post_content}")
