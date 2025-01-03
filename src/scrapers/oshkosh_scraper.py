import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import argparse
import json

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

class OshkoshScraper(BaseScraper):
    def __init__(self, config, test_run=False):
        super().__init__(config)
        self.driver = self.initialize_driver()
        self.test_run = test_run

    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        return driver

    def scroll_to_bottom(self, driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    def extract_event_links(self, soup, base_url):
        links = []
        anchor_tags = soup.find_all('a', href=True)
        for tag in anchor_tags:
            href = tag['href']
            if re.search(r'/event/.*/\d{6,}/$', href):
                full_url = base_url + href
                if full_url not in links:  # Avoid duplicates
                    links.append(full_url)
        return links

    def is_next_button_present(self, driver):
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'nxt'))
            )
            return next_button
        except Exception:
            return None

    def scrape_all_event_links(self, start_url, base_url, max_pages=10):
        all_links = []
        visited_pages = set()
        page_count = 0

        try:
            self.driver.get(start_url)
            while page_count < max_pages:
                current_url = self.driver.current_url
                if current_url in visited_pages:
                    break
                visited_pages.add(current_url)
                page_count += 1

                self.scroll_to_bottom(self.driver)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                event_links = self.extract_event_links(soup, base_url)
                all_links.extend(event_links)

                next_button = self.is_next_button_present(self.driver)
                if next_button:
                    next_button.click()
                    time.sleep(3)  # Wait for the next page to load
                else:
                    break

            time.sleep(5)
        except Exception as e:
            pass
        finally:
            self.driver.quit()

        # Remove duplicate links
        all_links = list(set(all_links))
        return all_links

    def scrape(self):
        base_url = "https://www.visitoshkosh.com"
        start_url = self.config['url']
        event_links = self.scrape_all_event_links(start_url, base_url)
        events = []

        for link in event_links:
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract structured data in JSON-LD format
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    event_data = json.loads(json_ld.string)
                    if event_data.get('@type') == 'Event':
                        events.append({
                            'name': event_data.get('name', 'N/A'),
                            'startDate': event_data.get('startDate', 'N/A'),
                            'endDate': event_data.get('endDate', 'N/A'),
                            'url': link,
                            'description': event_data.get('description', 'N/A'),
                            'location': event_data.get('location', {}).get('name', 'N/A'),
                            'address': event_data.get('location', {}).get('address', {}).get('streetAddress', 'N/A'),
                            'city': event_data.get('location', {}).get('address', {}).get('addressLocality', 'N/A'),
                            'region': event_data.get('location', {}).get('address', {}).get('addressRegion', 'N/A')
                        })
                except json.JSONDecodeError as e:
                    pass

        return events

    def process_data(self, data):
        # Implement the logic to process the scraped data
        processed_events = []
        for event in data:
            processed_events.append({
                'title': event['name'],
                'start_date': event['startDate'],
                'end_date': event['endDate'],
                'url': event['url'],
                'description': event['description'],
                'location': event['location'],
                'address': event['address'],
                'city': event['city'],
                'region': event['region']
            })
        return processed_events

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oshkosh Scraper")
    parser.add_argument("--test-run", action="store_true", help="Fetch only the first 3 events from the first page of links")
    args = parser.parse_args()

    # Example configuration for testing
    config = {
        'url': 'https://www.visitoshkosh.com/events/?bounds=false&view=list&sort=date'
    }
    scraper = OshkoshScraper(config, test_run=args.test_run)
    events = scraper.scrape()
    processed_events = scraper.process_data(events)
