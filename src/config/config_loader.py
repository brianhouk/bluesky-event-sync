import os
import json
import logging

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

def load_config(config_path):
    """Load configuration from JSON file"""
    logger.info(f"Loading configuration from {config_path}")
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def load_credentials():
    """Load credentials from environment variables based on usernames in config"""
    from .config_loader import load_config
    
    logger.info("Loading credentials from environment")
    config = load_config('config/config.json')
    accounts = []
    seen_usernames = set()

    for site in config['websites']:
        account_username = site['account_username']
        if account_username not in seen_usernames:
            seen_usernames.add(account_username)
            env_key = f"BLUESKY_{account_username.split('.')[0].upper()}_PASSWORD"
            password = os.getenv(env_key)
            if not password:
                logger.error(f"Environment variable '{env_key}' not set")
                raise ValueError(f"Environment variable '{env_key}' is not set")
            logger.info(f"Loaded credentials for {account_username}")
            accounts.append({"username": account_username, "password": password})

    return {"accounts": accounts}