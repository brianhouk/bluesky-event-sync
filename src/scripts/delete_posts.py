import sys
import os
import logging
import argparse
from atproto import Client
from src.config.config_loader import load_config
from src.bluesky.auth import authenticate

## Set password environment variable
# export BLUESKY_DISCOVEROSHKOSH_PASSWORD=your_password
#
# Run script with debug output
# PYTHONPATH=$(pwd) python3 src/scripts/delete_posts.py discoveroshkosh.bsky.social

# Set up logging to both file and console with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def delete_all_posts(username, password):
    """Delete all posts for a given Bluesky account."""
    logger.debug(f"Starting deletion process for {username}")
    
    try:
        # Initialize client
        logger.debug("Creating Bluesky client")
        client = Client()
        
        # Attempt login
        logger.debug("Attempting to login")
        client.login(username, password)
        logger.info(f"Successfully logged in as {username}")
        
        deleted_count = 0
        cursor = None
        
        while True:
            logger.debug(f"Fetching posts (cursor: {cursor})")
            feed = client.get_author_feed(actor=username, cursor=cursor)
            
            if not feed.feed:
                logger.info("No posts found")
                break
            
            for post in feed.feed:
                try:
                    logger.info(f"Deleting post: {post.post.record.text[:50]}...")
                    client.delete_post(post.post.uri)
                    deleted_count += 1
                    print(f"Deleted post {deleted_count}")
                except Exception as e:
                    logger.error(f"Failed to delete post: {e}")
            
            cursor = feed.cursor
            if not cursor:
                break
                
        logger.info(f"Finished. Deleted {deleted_count} posts")
        
    except Exception as e:
        logger.error(f"Error in deletion process: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete all posts for a Bluesky account")
    parser.add_argument("username", help="Bluesky username (e.g., username.bsky.social)")
    args = parser.parse_args()
    
    # Get password from environment
    env_var = f"BLUESKY_{args.username.split('.')[0].upper()}_PASSWORD"
    password = os.getenv(env_var)
    
    if not password:
        logger.error(f"No password found in environment variable {env_var}")
        sys.exit(1)
    
    logger.debug(f"Found password in environment variable {env_var}")
    delete_all_posts(args.username, password)