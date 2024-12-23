import os
import json

def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def load_credentials():
    return {
        "accounts": [
            {
                "username": os.getenv("BLUESKY_USERNAME_1"),
                "password": os.getenv("BLUESKY_PASSWORD_1")
            },
            {
                "username": os.getenv("BLUESKY_USERNAME_2"),
                "password": os.getenv("BLUESKY_PASSWORD_2")
            }
        ]
    }