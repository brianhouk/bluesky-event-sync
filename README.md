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
   ```
   export BLUESKY_USERNAME_1=your_username_1 export BLUESKY_PASSWORD_1=your_password_1 export BLUESKY_USERNAME_2=your_username_2 export BLUESKY_PASSWORD_2=your_password_2
   ```

## Environment Variables
To avoid storing sensitive credentials in the configuration files, use environment variables. Set the following environment variables before running the application:

- `BLUESKY_USERNAME_1`: The username for the first Bluesky account.
- `BLUESKY_PASSWORD_1`: The password for the first Bluesky account.
- `BLUESKY_USERNAME_2`: The username for the second Bluesky account.
- `BLUESKY_PASSWORD_2`: The password for the second Bluesky account.

You can set these environment variables in your shell or in a `.env` file if you are using Docker Compose.

Example:
```sh
export BLUESKY_USERNAME_1=your_username_1
export BLUESKY_PASSWORD_1=your_password_1
export BLUESKY_USERNAME_2=your_username_2
export BLUESKY_PASSWORD_2=your_password_2
```

## Running the Application
To run the application, use Docker:
```
docker-compose up
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.