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
        logging.FileHandler('selenium_scraping.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OshkoshScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.driver = self.initialize_driver()

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
                    logger.debug(f'Extracted event link: {full_url}')
        return links

    def is_next_button_present(self, driver):
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'nxt'))
            )
            logger.debug('Next button is present and clickable.')
            return next_button
        except Exception:
            logger.debug('Next button is not present or not clickable.')
            return None

    def scrape_all_event_links(self, start_url, base_url, max_pages=10):
        logger.debug('Starting to scrape all event links...')
        all_links = []
        visited_pages = set()
        page_count = 0

        try:
            self.driver.get(start_url)
            while page_count < max_pages:
                current_url = self.driver.current_url
                if current_url in visited_pages:
                    logger.warning(f'Already visited {current_url}. Ending pagination.')
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
                    logger.info('No next button found. Reached the last page.')
                    break

            logger.debug('Waiting for 5 seconds before closing the browser...')
            time.sleep(5)
        except Exception as e:
            logger.critical(f'An unexpected error occurred: {e}')
        finally:
            self.driver.quit()
            logger.debug('WebDriver closed.')

        # Remove duplicate links
        all_links = list(set(all_links))
        logger.info(f'Total unique event links scraped: {len(all_links)}')
        return all_links

    def scrape(self):
        base_url = "https://www.visitoshkosh.com"
        start_url = self.config['url']
        event_links = self.scrape_all_event_links(start_url, base_url)
        events = []

        for link in event_links:
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            title_element = soup.select_one('h1.event-title')
            date_element = soup.select_one('dl.priority-info dd')
            time_element = soup.select_one('dl dd:contains("Time:")')
            if title_element and date_element:
                title = title_element.get_text(strip=True)
                date_str = date_element.get_text(strip=True)
                try:
                    if 'to' in date_str:
                        start_date_str, end_date_str = date_str.split(' to ')
                        start_date = datetime.strptime(start_date_str.strip(), '%B %d, %Y')
                        end_date = datetime.strptime(end_date_str.strip(), '%B %d, %Y')
                    else:
                        start_date = end_date = datetime.strptime(date_str.strip(), '%B %d, %Y')
                except ValueError as e:
                    logger.error(f"Error parsing date: {date_str} - {e}")
                    continue

                time_str = time_element.get_text(strip=True) if time_element else ''
                events.append({
                    'title': title,
                    'start_date': start_date,
                    'end_date': end_date,
                    'time': time_str,
                    'url': link
                })
                logger.debug(f"Added event: {title} from {start_date} to {end_date} at {time_str}")

        logger.debug(f"Scraping completed with {len(events)} events found")
        return events

    def process_data(self, data):
        # Implement the logic to process the scraped data
        processed_events = []
        for event in data:
            processed_events.append({
                'title': event['title'],
                'start_date': event['start_date'],
                'end_date': event['end_date'],
                'time': event.get('time', ''),
                'url': event['url']
            })
        logger.debug(f"Processed {len(processed_events)} events")
        return processed_events

if __name__ == "__main__":
    # Example configuration for testing
    config = {
        'url': 'https://www.visitoshkosh.com/events/?bounds=false&view=list&sort=date'
    }
    scraper = OshkoshScraper(config)
    events = scraper.scrape()
    processed_events = scraper.process_data(events)
    print("Scraped Events:")
    for event in processed_events:
        print(event)
