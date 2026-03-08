# yt-dlp-bot

A Discord bot for downloading and tracking YouTube videos and streams using `yt-dlp` and `streamlink`.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/yt-dlp-bot.git
    cd yt-dlp-bot
    ```

2.  **Install dependencies**:
    ```bash
    pipx run poetry install
    ```

## Configuration

Copy `bot.json.default` to `bot.json` and fill in your details:

```json
{
    "discord_key": "YOUR_DISCORD_BOT_TOKEN",
    "database_file": "bot.db",
    "yt_dlp_config": {
        "paths": {
            "home": "/path/to/downloads"
        }
    },
    "use_streamlink_for_subscriptions": true
}
```

- `discord_key`: Your Discord bot token.
- `database_file`: Path to the SQLite database file.
- `yt_dlp_config`: Standard `yt-dlp` options.
- `use_streamlink_for_subscriptions`: Whether to use streamlink for automatic subscription downloads.

## Running the Bot

Start the bot using Poetry:

```bash
pipx run poetry run python yt_dlp_bot/main.py
```

Optional arguments:
- `--log-level`: Sets the log level (e.g., `DEBUG`, `INFO`).
- `--config-file`: Path to your config file (defaults to `bot.json`).

## Testing

Run the test suite with coverage:

```bash
pipx run poetry run pytest --cov=yt_dlp_bot --cov-report=term-missing
```

## Documentation

For more detailed information, see the `docs/` folder:
- [Project Structure](docs/project_structure.md)
- [Bot Commands](docs/bot_commands.md)
- [Database Schema](docs/database_schema.md)
