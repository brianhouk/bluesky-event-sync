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

class BaseScraper:
    def __init__(self, config):
        self.config = config

    def scrape(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def handle_data(self, data):
        raise NotImplementedError("Subclasses should implement this method.")

    def log(self, message):
        print(f"[LOG] {message}")