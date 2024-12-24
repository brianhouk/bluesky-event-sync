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
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WinnebagoScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)

    def scrape(self):
        events = []
        page = 0
        while True:
            url = f"{self.config['url']}?page={page}"
            logger.debug(f"Scraping URL: {url}")
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            event_elements = soup.select('.views-row')
            logger.debug(f"Found {len(event_elements)} event elements on page {page}")

            if not event_elements:
                break

            for event_element in event_elements:
                title_element = event_element.select_one('.views-field-title a')
                date_elements = event_element.select('.views-field-field-date-time .datetime')
                if title_element and date_elements:
                    title = title_element.get_text(strip=True)
                    url = title_element['href']
                    for date_element in date_elements:
                        date_str = date_element.get_text(strip=True)
                        try:
                            date = datetime.strptime(date_str, '%A, %B %d, %Y - %H:%M')
                        except ValueError as e:
                            logger.error(f"Error parsing date: {date_str} - {e}")
                            continue
                        events.append({
                            'title': title,
                            'date': date,
                            'url': url
                        })
                        logger.debug(f"Added event: {title} on {date}")

            page += 1

        logger.debug(f"Scraping completed with {len(events)} events found")
        return events

    def process_data(self, data):
        # Implement the logic to process the scraped data
        processed_events = []
        for event in data:
            processed_events.append({
                'title': event['title'],
                'date': event['date'],
                'url': event['url']
            })
        logger.debug(f"Processed {len(processed_events)} events")
        return processed_events

if __name__ == "__main__":
    # Example configuration for testing
    config = {
        'url': 'https://www.co.winnebago.wi.us/parks/sunnyview-exposition-center/event-calendar-upcoming-list'
    }
    scraper = WinnebagoScraper(config)
    events = scraper.scrape()
    processed_events = scraper.process_data(events)
    print("Scraped Events:")
    for event in processed_events:
        print(event)