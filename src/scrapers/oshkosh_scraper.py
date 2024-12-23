import feedparser
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper

class OshkoshScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)

    def scrape(self):
        feed = feedparser.parse(self.config['url'])
        events = []

        for entry in feed.entries:
            title = entry.title
            date_str = entry.published
            date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            url = entry.link
            events.append({
                'title': title,
                'date': date,
                'url': url
            })

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
        return processed_events