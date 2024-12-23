class BaseScraper:
    def __init__(self, config):
        self.config = config

    def scrape(self):
        raise NotImplementedError("Scrape method must be implemented by subclasses.")

    def process_data(self, data):
        raise NotImplementedError("Process data method must be implemented by subclasses.")


class OshkoshScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)

    def scrape(self):
        # Implement the scraping logic for Oshkosh events
        # This is a placeholder for the actual scraping code
        events = []
        # Example scraping logic would go here
        return events

    def process_data(self, data):
        # Implement the logic to process the scraped data
        # This is a placeholder for the actual data processing code
        processed_events = []
        # Example data processing logic would go here
        return processed_events