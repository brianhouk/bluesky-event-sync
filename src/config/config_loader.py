import os
import json

def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

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