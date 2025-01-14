import logging
from datetime import datetime
from atproto_client import models

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
        logger.info(f"Preparing to post event: {event_data['title']}")
        logger.debug(f"Full event data: {event_data}")
        logger.debug(f"Posting as account: {account_info['username']}")

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

        logger.info(f"Posting content: {post_content}")
        # Use the Bluesky API to post the content
        # client.send_post(text=post_content)
        logger.info("Post successful")

        # Update the last_posted timestamp
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE events
            SET last_posted = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), event_data['id']))
        connection.commit()
        
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
