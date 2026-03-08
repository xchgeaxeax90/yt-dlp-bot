# Project Structure and Component Functioning

This document outlines the structure of the `yt-dlp-bot` project and describes the function of its main components.

## Project Overview

The `yt-dlp-bot` is a Discord bot designed to facilitate media downloads, primarily using `yt-dlp` and `streamlink`. It can download videos immediately, schedule downloads for future availability (e.g., for upcoming streams), and subscribe to YouTube channels for automatic downloads. The bot integrates with a `pikl_api` for external notifications and management of waiting rooms and stream notifications.

## Top-Level Directory Structure

*   `.gitignore`: Specifies intentionally untracked files to ignore.
*   `AGENTS.md`: Documentation for agents.
*   `bot.json.default`: Default bot configuration.
*   `Dockerfile`: Defines the Docker image for the application.
*   `poetry.lock`, `pyproject.toml`: Poetry dependency management files for Python.
*   `agent/`: Contains agent-related files, such as `refactoring_plan.md`.
*   `docs/`: Project documentation.
*   `tests/`: Contains unit and integration tests for the project.
*   `yt_dlp_bot/`: The core application source code.

## `yt_dlp_bot/` Application Structure

This directory contains the main logic and components of the Discord bot.

*   `bot.py`:
    *   Defines the `YtDlpBot` class, which extends `discord.ext.commands.Bot`.
    *   Sets the default command prefix for the bot to `y?`.

*   `main.py`:
    *   The primary entry point for the application.
    *   Responsible for setting up logging, Discord intents, and initializing the `YtDlpBot` instance.
    *   Establishes the database connection and initializes various repositories and services.
    *   Adds Discord Cogs (`sync`, `ytdl`, `subscription`, `system`) to the bot.

*   `database.py`:
    *   Handles the initialization and schema creation for the SQLite database.

*   `helpers.py`:
    *   Contains helper functions and utilities used across the application.
    *   Manages configuration settings using Pydantic models.

*   `views.py`:
    *   Contains generic Discord UI components, such as `PaginatedView`, which provides base logic for button-based pagination in embeds.

*   `cogs/`:
    *   This directory holds Discord "cogs" – modular extensions that encapsulate commands.
    *   `sync.py`: Responsible for synchronizing Discord commands.
    *   `ytdl.py`: The main cog for YouTube-DL functionality.
        *   Contains commands like `download`, `scheduled-download`, `streamlink-download`, `get-running-downloads`, `get-scheduled-downloads`, and `cancel`.
    *   `subscription.py`: Manages YouTube channel subscriptions.
    *   `system.py`: Provides system management commands.
        *   `system df`: Checks disk usage of the download directory.
        *   `system list`: Lists tracked downloaded files with pagination.
        *   `system delete <id>`: Deletes a tracked file from disk and database.
        *   `system purge`: Removes database records for files that no longer exist on disk.
        *   `system scan`: Checks availability of tracked URLs using `yt-dlp`.

*   `pikl_api/`:
    *   Handles integration with an external "Pikl API" for managing waiting rooms and stream notifications.

*   `repositories/`:
    *   `download_repository.py`: Manages database operations related to downloads, including tracking `downloaded_files` and `future_downloads`.
    *   `subscription_repository.py`: Manages database operations related to channel subscriptions.

*   `services/`:
    *   `downloader.py`:
        *   Handles metadata extraction and availability checks using `yt-dlp`.
        *   Determines if a video is `AvailableNow`, `AvailableFuture`, or an `AvailabilityError`.
    *   `download_manager.py`:
        *   Manages the execution of active downloads using `yt-dlp` and `streamlink`.
        *   Tracks running tasks and handles cancellation via `threading.Event`.
        *   Records successful downloads into the `downloaded_files` table.
    *   `download_service.py`: Provides a high-level interface for initiating and scheduling downloads.
    *   `notification_service.py`: Handles sending notifications back to Discord.
    *   `scheduler_service.py`: Manages periodic tasks like checking for deferred downloads.
    *   `subscription_service.py`: Manages user subscriptions and handles incoming stream notifications.

## Configuration

The bot uses a `Config` model defined in `helpers.py`, supporting settings like `discord_key`, `database_file`, `yt_dlp_config`, `streamlink_config`, and `use_streamlink_for_subscriptions`.

## Running the Bot

The bot is started by executing `main.py`. It requires Python >= 3.11 and the Deno JS runtime for `yt-dlp`.
