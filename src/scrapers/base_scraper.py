class BaseScraper:
    def __init__(self, config):
        self.config = config

    def scrape(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def handle_data(self, data):
        raise NotImplementedError("Subclasses should implement this method.")

    def log(self, message):
        print(f"[LOG] {message}")