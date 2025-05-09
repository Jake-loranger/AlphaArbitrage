# Alpha Bot

A Python-based bot that performs scheduled API actions at configurable intervals.

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings:
   ```bash
   cp .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Bot

### Local Development
```bash
python src/main.py
```

### Docker
Build the container:
```bash
docker build -t alpha-bot .
```

Run the container:
```bash
docker run -d --env-file .env alpha-bot
```

## Configuration

The bot can be configured through environment variables in the `.env` file:

- `API_BASE_URL`: Base URL for the API
- `API_KEY`: API authentication key
- `INTERVAL_SECONDS`: Time between actions in seconds
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CONTAINER_NAME`: Name for the container

## Logging

Logs are stored in the `logs` directory with daily rotation and 7-day retention.

## Multiple Instances

To run multiple instances of the bot, you can:
1. Use different `.env` files for each instance
2. Run multiple containers with different environment configurations
3. Use Docker Compose for orchestration (coming soon) 