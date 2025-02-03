import pytest
from src.scrapers.base_scraper import BaseScraper, logger

# src/scrapers/test_base_scraper.py

# Dummy subclass to allow instantiation and testing of BaseScraper functionality.
class DummyScraper(BaseScraper):
    def scrape(self):
        logger.info("DummyScraper.scrape: called")
        return "scraped data"
    # Do not override handle_data to use the BaseScraper implementation.

def test_init_config():
    # Test that config is stored correctly.
    config = {"key": "value"}
    scraper = DummyScraper(config)
    assert scraper.config == config

def test_scrape_method():
    # Test that the implemented scrape method returns expected data.
    scraper = DummyScraper({})
    result = scraper.scrape()
    assert result == "scraped data"

def test_handle_data_not_implemented():
    # Since DummyScraper doesn't override handle_data, it should raise NotImplementedError.
    scraper = DummyScraper({})
    with pytest.raises(NotImplementedError) as exc_info:
        scraper.handle_data("sample data")
    assert "Subclasses should implement this method." in str(exc_info.value)

def test_log_method(capsys):
    # Test that log prints a message to stdout.
    scraper = DummyScraper({})
    scraper.log("Test message")
    captured = capsys.readouterr().out.strip()
    assert captured == "[LOG] Test message"