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
- Automatically backs up the database daily and retains the last five backups.

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

4. Set up environment variables for your Bluesky credentials and other configurations.

## Environment Variables
To avoid storing sensitive credentials in the configuration files, use environment variables. Set the following environment variables before running the application. When using Docker, you can specify these variables in a `.env` file at the project root – Docker Compose will automatically load them.

- `BLUESKY_DISCOVEROSHKOSH_PASSWORD`: The password for the `discoveroshkosh` Bluesky account.
- `BLUESKY_WISCONSINEVENTS_PASSWORD`: The password for the `wisconsinevents` Bluesky account.
- `PROD`: Set this variable to `TRUE` to enable posting to Bluesky. If not set, the application will run in dry-run mode and only log the event data.
- `SKIP_SCRAPING`: Set this variable to `TRUE` to skip the scraping process and only post events from the database.
- `MAX_POSTS`: Limits the number of posts to Bluesky. If not set, there is no limit.

Example:
```sh
export BLUESKY_DISCOVEROSHKOSH_PASSWORD=your_password_for_discoveroshkosh
export BLUESKY_WISCONSINEVENTS_PASSWORD=your_password_for_wisconsinevents
export PROD=TRUE
export SKIP_SCRAPING=TRUE
export MAX_POSTS=2
```

## Running the Application
You can run the application either via Docker or directly:

### Using Docker
```sh
docker-compose up
```

### Direct Execution
By default, the application runs in dry-run mode (only logging event data). To run in dry-run mode:
```sh
python src/main.py --dry-run
```

If you have set the environment variable `PROD=TRUE`, the application will post events to Bluesky.

## Options and Flags
The following command-line options are available:

- `--dry-run`: Runs the application without making actual posts to Bluesky. Instead, event data is logged.
- `--config <file>`: Specify an alternate configuration file (default: `config/config.json`).
- Additional flags may be added as the project evolves.

Refer to the project's code in [`src/main.py`](src/main.py) for the latest options.

## Running in Debug Mode
To run the application in debug mode with verbose logging, use the `--debug` flag when executing the application directly:

```sh
python src/main.py --debug
```

When using Docker, ensure that your `.env` file is configured with the desired environment variables. Then run:

```sh
docker-compose up
```

The debug mode will provide detailed output to help diagnose issues during development.

## Database Backup
The application automatically backs up the database daily and retains the last five backups. The backup script is located at backup_database.py.

## Running Tests
To run the tests, use the following command:

```
pytest --cov=src/ tests/
```
## Continuous Integration
The project includes a GitHub Actions workflow for continuous integration. The workflow is defined in ci.yml and runs the tests on every push to the main branch.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.