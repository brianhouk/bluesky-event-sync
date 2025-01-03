import logging
from abc import ABC, abstractmethod
from selenium import webdriver

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

class BaseScraper(ABC):
    def __init__(self, config):
        logger.info(f"BaseScraper.__init__: Initializing scraper with config: {config}")
        try:
            self.config = config
        except Exception as e:
            logger.error(f"BaseScraper.__init__: Failed: {e}")
            raise
        logger.info("BaseScraper.__init__: Initialization complete")

    @abstractmethod
    def scrape(self):
        logger.info("BaseScraper.scrape: Starting scrape operation")
        raise NotImplementedError("Subclasses should implement this method.")

    def handle_data(self, data):
        raise NotImplementedError("Subclasses should implement this method.")

    def log(self, message):
        print(f"[LOG] {message}")