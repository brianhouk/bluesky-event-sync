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
        super().__init__(config)
        self.base_url = config['url']

    def scrape(self):
        events = []
        page = 0
        while True:
            url = f"{self.base_url}?page={page}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            event_elements = soup.select('.views-row')

            if not event_elements:
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
                            continue
                        # Check if the event already exists
                        existing_event = next((event for event in events if event['title'] == title and event['url'] == full_url), None)
                        if existing_event:
                            # Update the end date if the new date is later
                            if date > existing_event['end_date']:
                                existing_event['end_date'] = date
                        else:
                            # Add a new event with start and end date
                            events.append({
                                'title': title,
                                'start_date': date,
                                'end_date': date,
                                'url': full_url
                            })

            page += 1

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