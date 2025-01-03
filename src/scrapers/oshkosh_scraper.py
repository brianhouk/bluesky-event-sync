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
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluesky-event-sync.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OshkoshScraper(BaseScraper):
    def __init__(self, config, test_run=False):
        logger.info("OshkoshScraper.__init__: Starting initialization")
        super().__init__(config)
        self.test_run = test_run
        logger.info("OshkoshScraper.__init__: Setting up webdriver")
        self.driver = self.initialize_driver()
        logger.info("OshkoshScraper.__init__: Initialization complete")

    def initialize_driver(self):
        logger.info("initialize_driver: Setting up Chrome options")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        logger.info("initialize_driver: Creating Chrome driver")
        try:
            driver = webdriver.Chrome(options=options)
            logger.info("initialize_driver: Chrome driver created successfully")
            return driver
        except Exception as e:
            logger.error(f"initialize_driver: Failed to create Chrome driver: {e}", exc_info=True)
            raise

    def scroll_to_bottom(self, driver):
        logger.info("scroll_to_bottom: Starting page scroll")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            logger.info("scroll_to_bottom: Waiting for content to load")
            time.sleep(3)
            logger.info("scroll_to_bottom: Scroll complete")
        except Exception as e:
            logger.error(f"scroll_to_bottom: Error during scrolling: {e}", exc_info=True)
            raise

    def extract_event_links(self, soup, base_url):
        logger.info("extract_event_links: Starting link extraction")
        links = []
        try:
            anchor_tags = soup.find_all('a', href=True)
            logger.info(f"extract_event_links: Found {len(anchor_tags)} anchor tags")
            
            for tag in anchor_tags:
                href = tag['href']
                if re.search(r'/event/.*/\d{6,}/$', href):
                    full_url = base_url + href
                    if full_url not in links:
                        links.append(full_url)
                        logger.debug(f"extract_event_links: Added new link: {full_url}")
            
            logger.info(f"extract_event_links: Extracted {len(links)} unique event links")
            return links
        except Exception as e:
            logger.error(f"extract_event_links: Error during link extraction: {e}", exc_info=True)
            raise

    def is_next_button_present(self, driver):
        logger.info("is_next_button_present: Checking for next button")
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'nxt'))
            )
            logger.info("is_next_button_present: Next button found")
            return next_button
        except Exception as e:
            logger.info("is_next_button_present: No next button found")
            return None

    def scrape_all_event_links(self, start_url, base_url, max_pages=10):
        logger.info(f"scrape_all_event_links: Starting with URL {start_url}")
        all_links = []
        page = 1
        
        try:
            logger.info("scrape_all_event_links: Loading initial page")
            self.driver.get(start_url)
            
            while page <= max_pages:
                logger.info(f"scrape_all_event_links: Processing page {page}")
                self.scroll_to_bottom(self.driver)
                
                logger.info("scrape_all_event_links: Parsing page content")
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                page_links = self.extract_event_links(soup, base_url)
                logger.info(f"scrape_all_event_links: Found {len(page_links)} links on page {page}")
                all_links.extend(page_links)
                
                next_button = self.is_next_button_present(self.driver)
                if not next_button:
                    logger.info("scrape_all_event_links: No more pages available")
                    break
                    
                logger.info(f"scrape_all_event_links: Navigating to page {page + 1}")
                next_button.click()
                time.sleep(3)
                page += 1
                
        except Exception as e:
            logger.error(f"scrape_all_event_links: Error occurred: {e}", exc_info=True)
            raise
            
        logger.info(f"scrape_all_event_links: Complete. Total links found: {len(all_links)}")
        return all_links

    def scrape(self):
        base_url = "https://www.visitoshkosh.com"
        start_url = self.config['url']
        event_links = self.scrape_all_event_links(start_url, base_url)
        events = []

        for link in event_links:
            logger.debug(f"Processing event link: {link}")
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract structured data in JSON-LD format
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    event_data = json.loads(json_ld.string)
                    if event_data.get('@type') == 'Event':
                        logger.debug(f"Extracted JSON-LD: {event_data}")
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
                    logger.error(f"Error parsing JSON-LD: {e}")

        logger.debug(f"Scraping completed with {len(events)} events found")
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
        logger.debug(f"Processed {len(processed_events)} events")
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
    logger.info(f"Main: Processed events: {processed_events}")