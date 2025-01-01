# README.md

# Bluesky Event Publisher

## Overview
The Bluesky Event Publisher is a Python application designed to scrape events from public calendars and repost them to Bluesky at specified intervals. The application is modular, allowing for the addition of multiple scraping sources and configurations.

## Features
- Scrapes events from specified websites.
- Posts events to Bluesky at configurable intervals.
- Supports multiple Bluesky accounts.
- Configurable via JSON files.
- Runs in Docker with SQLite as the datastore.
- Dry-run mode for testing without making actual posts or database changes.

## Project Structure
```
bluesky-event-publisher
├── src
│   ├── config
│   ├── scrapers
│   ├── database
│   ├── bluesky
│   └── main.py
├── config
├── tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd bluesky-event-publisher
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application by editing the `config/config.json` file.

4. Set up environment variables for your Bluesky credentials:

## Environment Variables
To avoid storing sensitive credentials in the configuration files, use environment variables. Set the following environment variables before running the application:

- `BLUESKY_DISCOVEROSHKOSH_PASSWORD`: The password for the `discoveroshkosh` Bluesky account.
- `BLUESKY_WISCONSINEVENTS_PASSWORD`: The password for the `wisconsinevents` Bluesky account.
- `PROD`: Set this variable to `true` to enable posting to Bluesky. If not set, the application will run in dry-run mode and only log the event data.

You can set these environment variables in your shell or in a `.env` file if you are using Docker Compose.

Example:
```sh
export BLUESKY_DISCOVEROSHKOSH_PASSWORD=your_password_for_discoveroshkosh
export BLUESKY_WISCONSINEVENTS_PASSWORD=your_password_for_wisconsinevents
export PROD=true
```

## Running the Application
To run the application, use Docker:
```
docker-compose up
```

To run the application in dry-run mode:
```
python src/main.py --dry-run
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.