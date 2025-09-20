# x_to_discord

`x_to_discord` monitors a target X (Twitter) account and forwards fresh tweets to a Discord channel via webhook. It keeps track of the last delivered tweet, honours your filtering preferences, and can optionally translate English posts into Traditional Chinese before posting.

## Features
- Polls X API v2 through Tweepy with automatic rate-limit handling.
- Filters replies/retweets, controls polling interval, and limits batch size per request.
- Formats messages for Discord with timestamps, permalinks, and optional translations.
- Persists the last processed tweet ID in `state.json` so restarts do not resend content.
- Includes a lightweight translation helper that can call MyMemory or LibreTranslate.
- Offers `fake_mode` (record/replay) to develop without hitting the live X API.

## Requirements
- Python 3.10+
- X (Twitter) developer Bearer Token
- Discord webhook URL for the target channel
- (Recommended) Poetry 1.6+ for dependency management

## Getting Started
1. Clone the repository and enter the project folder.
   ```powershell
   git clone https://github.com/starazzip/x_to_discord.git
   cd x_to_discord
   ```
2. Install dependencies (choose one approach).
   - **Poetry (recommended)**
     ```powershell
     poetry install
     ```
   - **Virtual environment + pip**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     pip install tweepy requests python-dotenv
     ```
3. Create your configuration.
   ```powershell
   copy .env.example .env  # Windows PowerShell
   ```
   Fill in the required values described below.
4. Run the poller.
   ```powershell
   poetry run python main.py
   ```
   Or activate your virtual environment and execute `python main.py` directly.

## Configuration
### Required
- `BEARER_TOKEN`: X API Bearer Token for the app.
- `TARGET_USERNAME`: Screen name (without `@`) to monitor.
- `DISCORD_WEBHOOK_URL`: Target Discord webhook endpoint.

### Behaviour
- `USER_ID`: Numeric user id (skips username lookup when provided).
- `POLL_INTERVAL_SECONDS`: Delay between fetches (default: 60 seconds).
- `EXCLUDE_REPLIES` / `EXCLUDE_RETWEETS`: Filter replies or retweets (default: `true`).
- `CATCH_UP_ON_FIRST_RUN`: Send older tweets on first run (default: `false`).
- `STATE_FILE`: Path to the JSON state file (default: `state.json`).
- `MAX_RESULTS`: Items per API call, clamped to 5-100 (default: `10`).
- `EMBED_DOMAIN`: Domain used in Discord permalinks (default: `twitter.com`).

### Translation
- `INCLUDE_TRANSLATION`: Enable translated content in Discord messages (default: `true`).
- `TRANSLATE_PROVIDER`: `none` or `ultra` (default: `none`).
- `ULTRA_PROVIDER_ORDER`: Priority list, e.g. `mymemory,libre`.
- `ULTRA_FREE_LIMIT`: Character limit per translation chunk (max 400).
- `FREE_TRANSLATE_ENDPOINT` / `FREE_TRANSLATE_API_KEY`: Optional LibreTranslate endpoint and key.

### Fake data helpers
- `FAKE_MODE`: `off`, `record`, or `replay`.
  - `record`: Call X and append tweets into the fake data JSON.
  - `replay`: Serve tweets from fake data without calling the API.
- `FAKE_DIR`: Directory for fake fixtures (default: `fake_data`).
- `FAKE_FILE`: Filename inside `FAKE_DIR` (default: `fake_${TARGET_USERNAME}.json`).

## Project Layout
```
.
|-- main.py                # Entry point; polls X and forwards to Discord
|-- app/
|   |-- config.py          # Environment variable parsing and validation
|   |-- x_client.py        # X API client wrapper with fake-mode support
|   |-- formatter.py       # Discord message builder and translation glue
|   |-- discord_sender.py  # Discord webhook sender with rate-limit handling
|   |-- state_store.py     # JSON persistence for last seen tweet ids
|   |-- translate_ultra.py # Chunked translation helpers + HTTP clients
|   `-- fake_io.py         # Fake data serialization utilities
|-- tests/
|   `-- test_translate_ultra.py
|-- .env.example
|-- pyproject.toml
`-- poetry.lock
```

## Runtime Overview
1. Load `.env` and build the `Config` dataclass.
2. Initialise the Tweepy client and resolve the user id.
3. Read the last seen tweet id from `state.json`.
4. Poll X for new tweets, optionally translate, and format them for Discord.
5. Deliver the message through the webhook and persist the new last seen id.

## Testing
Use the built-in unit tests to verify the translation utilities.
```powershell
poetry run python -m unittest
```

## Notes
- Keep `CATCH_UP_ON_FIRST_RUN=false` if you only want tweets published after the first launch.
- `discord_sender.post_discord` respects `Retry-After` headers to avoid rate limits.
- `fake_mode=replay` is ideal for demos or UI tweaks without calling live APIs.

## License
No license file is bundled yet. Add the appropriate LICENSE before publishing on GitHub.
