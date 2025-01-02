import os
import json
import logging

logger = logging.getLogger(__name__)

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def load_credentials(config):
    accounts = {}
    for website in config['websites']:
        username = website['account_username']
        password_env_var = f"BLUESKY_{username.upper()}_PASSWORD"
        password = os.getenv(password_env_var)
        if not password:
            logger.error(f"Environment variable {password_env_var} not set")
            raise ValueError(f"Environment variable {password_env_var} not set")
        if username not in accounts:
            accounts[username] = {
                "username": username,
                "password": password
            }
    return {"accounts": list(accounts.values())}