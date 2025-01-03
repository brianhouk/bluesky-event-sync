import os
import json

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def load_credentials():
    from .config_loader import load_config
    import os

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
                raise ValueError(f"Environment variable '{env_key}' is not set")
            accounts.append({"username": account_username, "password": password})

    return {"accounts": accounts}