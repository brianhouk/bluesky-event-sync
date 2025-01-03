import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import sys
import os

# Adjust imports based on how the script is run
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.base_scraper import BaseScraper
else:
    from .base_scraper import BaseScraper

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

class WinnebagoScraper(BaseScraper):
    def __init__(self, config):
        logger.info("WinnebagoScraper.__init__: Initializing scraper")
        super().__init__(config)
        self.base_url = config['url']
        logger.info("WinnebagoScraper.__init__: Initialization complete")

    def scrape(self):
        logger.info("scrape: Starting scrape operation")
        events = []
        page = 0
        while True:
            url = f"{self.base_url}?page={page}"
            logger.info(f"scrape: Fetching URL: {url}")
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            event_elements = soup.select('.views-row')
            logger.info(f"scrape: Found {len(event_elements)} event elements on page {page}")

            if not event_elements:
                logger.info("scrape: No more event elements found, ending scrape")
                break

            for event_element in event_elements:
                title_element = event_element.select_one('.views-field-title a')
                date_elements = event_element.select('.views-field-field-date-time .datetime')
                if title_element and date_elements:
                    title = title_element.get_text(strip=True)
                    relative_url = title_element['href']
                    full_url = self.base_url + relative_url
                    for date_element in date_elements:
                        date_str = date_element.get_text(strip=True)
                        try:
                            date = datetime.strptime(date_str, '%A, %B %d, %Y - %H:%M')
                        except ValueError as e:
                            logger.warning(f"scrape: Date parsing failed for {date_str}: {e}")
                            continue
                        existing_event = next((event for event in events if event['title'] == title and event['url'] == full_url), None)
                        if existing_event:
                            if date > existing_event['end_date']:
                                existing_event['end_date'] = date
                                logger.info(f"scrape: Updated end date for event {title}")
                        else:
                            events.append({
                                'title': title,
                                'start_date': date,
                                'end_date': date,
                                'url': full_url
                            })
                            logger.info(f"scrape: Added new event {title}")

            page += 1
            logger.info(f"scrape: Moving to next page {page}")

        logger.info(f"scrape: Completed with {len(events)} events found")
        return events

    def process_data(self, data):
        # Implement the logic to process the scraped data
        processed_events = []
        for event in data:
            processed_events.append({
                'title': event['title'],
                'start_date': event['start_date'].isoformat(),
                'end_date': event['end_date'].isoformat(),
                'url': event['url']
            })
        return processed_events