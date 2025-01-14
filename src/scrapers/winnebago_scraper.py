import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import sys
import os
from urllib.parse import urljoin

# Adjust imports based on how the script is run
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.base_scraper import BaseScraper
else:
    from .base_scraper import BaseScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WinnebagoScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = config['url']

    def scrape(self):
        events = []
        page = 0
        while True:
            url = f"{self.base_url}?page={page}"
            logger.info(f"Scraping page {page}: {url}")
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            event_elements = soup.select('.views-row')

            if not event_elements:
                logger.info("No more events found")
                break

            for event_element in event_elements:
                try:
                    # Required elements
                    title_element = event_element.select_one('.views-field-title a')
                    date_elements = event_element.select('.views-field-field-date-time .datetime')
                    
                    if title_element and date_elements:
                        title = title_element.get_text(strip=True)
                        relative_url = title_element['href']
                        full_url = urljoin(self.base_url, relative_url)

                        # Optional elements with defaults
                        desc_element = event_element.select_one('.views-field-field-description')
                        description = desc_element.get_text(strip=True) if desc_element else ""

                        location_element = event_element.select_one('.views-field-field-location')
                        location = location_element.get_text(strip=True) if location_element else ""

                        address_element = event_element.select_one('.views-field-field-address')
                        address = address_element.get_text(strip=True) if address_element else ""

                        for date_element in date_elements:
                            date_str = date_element.get_text(strip=True)
                            try:
                                date = datetime.strptime(date_str, '%A, %B %d, %Y - %H:%M')
                                
                                # Check for existing event
                                existing_event = next((event for event in events 
                                                    if event['title'] == title and event['url'] == full_url), None)
                                if existing_event:
                                    if date > existing_event['end_date']:
                                        existing_event['end_date'] = date
                                        logger.debug(f"Updated end date for {title}")
                                else:
                                    event = {
                                        'title': title,
                                        'start_date': date,
                                        'end_date': date,
                                        'url': full_url,
                                        'description': description,
                                        'location': location,
                                        'address': address,
                                        'city': 'Oshkosh',
                                        'region': 'WI'
                                    }
                                    logger.info(f"Added event: {title}")
                                    events.append(event)
                            except ValueError as e:
                                logger.warning(f"Invalid date format: {date_str} - {e}")
                                continue
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    continue

            page += 1

        logger.info(f"Scraping completed: {len(events)} events found")
        return events

    def process_data(self, data):
        # Implement the logic to process the scraped data
        processed_events = []
        for event in data:
            processed_events.append({
                'title': event['title'],
                'description': event['description'],
                'start_date': event['start_date'],
                'end_date': event['end_date'],
                'url': event['url']
            })
        return processed_events

if __name__ == "__main__":
    # Example configuration for testing
    config = {
        'url': 'https://www.co.winnebago.wi.us/parks/sunnyview-exposition-center/event-calendar-upcoming-list'
    }
    scraper = WinnebagoScraper(config)
    events = scraper.scrape()
    processed_events = scraper.process_data(events)
    for event in processed_events:
        print(event)