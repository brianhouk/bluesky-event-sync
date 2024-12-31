import os
import json

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def load_credentials():
    return {
        "accounts": [
            {
                "username": "discoveroshkosh",
                "password": os.getenv("BLUESKY_DISCOVEROSHKOSH_PASSWORD")
            },
            {
                "username": "wisconsinevents",
                "password": os.getenv("BLUESKY_WISCONSINEVENTS_PASSWORD")
            }
        ]
    }