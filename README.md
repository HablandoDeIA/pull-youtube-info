# pull-youtube-info

Fetch the latest uploads for a YouTube channel using the YouTube Data API v3. The script loads secrets from a `.env` file via `python-dotenv` and outputs the collected video metadata as JSON.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) for virtualenv and dependency management
- Python 3.10+
- A YouTube Data API v3 key

## Setup

1. Copy the sample environment file and update it with your credentials:
   ```bash
   cp demo.env .env
   # then edit .env to add your real API key
   ```
2. Create and activate a virtual environment managed by uv:
   ```bash
   uv venv
   source .venv/bin/activate
   ```
3. Install dependencies with uv:
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

Run the script with uv so dependencies are resolved from the virtual environment:
```bash
uv run python youtube_info.py
```
The command prints a JSON array describing the videos (title, description, YouTube link, and published date).

To query a different channel without editing `.env`, supply `--channel`:
```bash
uv run python youtube_info.py --channel AnotherChannelName
```
Or, when using the Makefile, pass the `CHANNEL` variable:
```bash
make run CHANNEL=AnotherChannelName
```

## Makefile targets

- `make venv` – create/refresh `.venv` using uv
- `make install` – install dependencies inside `.venv`
- `make run` – execute the script (loads `.env` automatically)
- `make clean` – remove the virtual environment

## Notes

- The script uses the `CHANNEL_USERNAME` environment variable by default, but `--channel` (or `make run CHANNEL=...`) takes precedence if provided.
- `CHANNEL_USERNAME` / `--channel` accepts either a username or channel ID (`UC...`). If the uploads playlist is unavailable, the script transparently falls back to listing videos via the search API.
- The YouTube Data API enforces quotas; plan for retries/backoff if you extend this script, and ensure "YouTube Data API v3" is enabled for your API key.
