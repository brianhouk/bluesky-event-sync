import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import json
import tempfile
import pytest
from src.config.config_loader import load_config, load_credentials

# src/config/test_config_loader.py


def test_load_config_success(tmp_path):
    # Prepare temporary configuration file
    config_data = {
        "websites": [
            {
                "name": "TestSite",
                "account_username": "testuser.bsky.social",
                "url": "http://example.com",
                "update_intervals": ["1 day"]
            }
        ]
    }
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_data))
    
    loaded_config = load_config(str(config_file))
    assert loaded_config == config_data

def test_load_config_failure(tmp_path):
    # Pass a non-existent file path
    non_existent_file = tmp_path / "nonexistent.json"
    with pytest.raises(Exception):
        load_config(str(non_existent_file))

def test_load_credentials_success(monkeypatch):
    # Monkeypatch load_config to return a predefined configuration.
    fake_config = {
        "websites": [
            {
                "name": "TestSite",
                "account_username": "testuser.bsky.social",
                "url": "http://example.com",
                "update_intervals": ["1 day"]
            },
            {
                "name": "AnotherSite",
                "account_username": "anothertest.bsky.social",
                "url": "http://example.org",
                "update_intervals": ["2 weeks"]
            }
        ]
    }
    monkeypatch.setattr("src.config.config_loader.load_config", lambda path: fake_config)
    
    # Set the corresponding environment variables.
    os.environ["BLUESKY_TESTUSER_PASSWORD"] = "secret1"
    os.environ["BLUESKY_ANOTHERTEST_PASSWORD"] = "secret2"
    
    credentials = load_credentials()
    accounts = credentials.get("accounts")
    assert accounts is not None
    # Should contain both accounts
    assert any(acc["username"] == "testuser.bsky.social" and acc["password"] == "secret1" for acc in accounts)
    assert any(acc["username"] == "anothertest.bsky.social" and acc["password"] == "secret2" for acc in accounts)
    
    # Clean up the environment variables
    del os.environ["BLUESKY_TESTUSER_PASSWORD"]
    del os.environ["BLUESKY_ANOTHERTEST_PASSWORD"]

def test_load_credentials_missing_env(monkeypatch):
    # Monkeypatch load_config to return a configuration with one website.
    fake_config = {
        "websites": [
            {
                "name": "TestSite",
                "account_username": "missinguser.bsky.social",
                "url": "http://example.com",
                "update_intervals": ["1 day"]
            }
        ]
    }
    monkeypatch.setattr("src.config.config_loader.load_config", lambda path: fake_config)
    
    # Ensure the environment variable is not set.
    env_key = "BLUESKY_MISSINGUSER_PASSWORD"
    if env_key in os.environ:
        del os.environ[env_key]
    
    with pytest.raises(ValueError):
        load_credentials()