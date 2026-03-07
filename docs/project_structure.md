# Project Structure and Component Functioning

This document outlines the structure of the `yt-dlp-bot` project and describes the function of its main components.

## Project Overview

The `yt-dlp-bot` is a Discord bot designed to facilitate media downloads, primarily using `yt-dlp` and `streamlink`. It can download videos immediately, schedule downloads for future availability (e.g., for upcoming streams), and subscribe to YouTube channels for automatic downloads. The bot integrates with a `pikl_api` for external notifications and management of waiting rooms and stream notifications.

## Top-Level Directory Structure

*   `.gitignore`: Specifies intentionally untracked files to ignore.
*   `AGENTS.md`: Documentation for agents (likely related to development or testing).
*   `bot.json.default`: Default bot configuration.
*   `Dockerfile`: Defines the Docker image for the application.
*   `poetry.lock`, `pyproject.toml`: Poetry dependency management files for Python.
*   `.env/`: Directory for environment variables.
*   `.git/`: Git version control directory.
*   `agent/`: Contains agent-related files, such as `refactoring_plan.md`.
*   `dist/`: Distribution or build artifacts.
*   `runtime/`: Runtime-specific files or configurations.
*   `tests/`: Contains unit and integration tests for the project.
*   `yt_dlp_bot/`: The core application source code.

## `yt_dlp_bot/` Application Structure

This directory contains the main logic and components of the Discord bot.

*   `bot.py`:
    *   Defines the `YtDlpBot` class, which extends `discord.ext.commands.Bot`.
    *   Sets the default command prefix for the bot to `y?`.
    *   This is the fundamental class that represents the Discord bot instance.

*   `main.py`:
    *   The primary entry point for the application.
    *   Responsible for setting up logging, Discord intents, and initializing the `YtDlpBot` instance.
    *   Establishes the database connection and initializes various repositories (`DownloadRepository`, `SubscriptionRepository`) and services (`DiscordNotificationService`).
    *   Initializes the `Downloader` with its dependencies.
    *   Conditionally sets up an `AsyncHttpClient` for the `pikl_api` if the `pikl_url` is configured.
    *   Adds Discord Cogs (`sync`, `ytdl`) to the bot.
    *   Starts the bot and gathers asynchronous tasks, including the `pikl_api` client if active.

*   `database.py`:
    *   Handles the initialization and schema creation for the SQLite database.
    *   Likely defines data models or utility functions for database interactions.

*   `helpers.py`:
    *   Contains helper functions and utilities used across the application.
    *   Manages configuration settings (e.g., `cli_args`, `config`).

*   `cogs/`:
    *   This directory holds Discord "cogs" – modular extensions that encapsulate commands, listeners, and other Discord.py features.
    *   `sync.py`: A cog likely responsible for synchronizing Discord commands or other bot state.
    *   `ytdl.py`: The main cog for YouTube-DL functionality.
        *   Contains Discord commands for users to interact with the download system (e.g., `download`, `scheduled-download`, `streamlink-download`, `df` for disk usage, `get-running-downloads`, `get-scheduled-downloads`, `cancel`, `subscribe`, `unsubscribe`).
        *   Manages parsing of time durations and Discord timestamps.
        *   Includes a background task (`check_tasks`) that periodically calls `Downloader.schedule_deferred_downloads` and `download_repository.cleanup_future_downloads`.

*   `downloader/`:
    *   Contains the core logic for handling media downloads.
    *   `downloader.py`:
        *   The `Downloader` class orchestrates `yt-dlp` and `streamlink` operations.
        *   **Availability Handling**: Determines if a video is `AvailableNow`, `AvailableFuture` (with an epoch timestamp), or an `AvailabilityError`.
        *   **Asynchronous Downloads**: Manages initiating and tracking multiple concurrent downloads using `asyncio.Task` and `threading.Event` for cancellation.
        *   **`_download`**: Internal method for executing `yt-dlp` downloads, including progress hooks and notification.
        *   **`_download_streamlink`**: Internal method for downloading via `streamlink`, including `ffmpeg` post-processing for muxing.
        *   **`download_async`**: Public method to start an immediate download.
        *   **`defer_download_until_time`**: Schedules a download to occur at a specified future time.
        *   **`schedule_deferred_downloads`**: A critical method called periodically to check for and initiate pending scheduled downloads. It manages the lifecycle of these tasks.
        *   **`cancel_download`**: Allows cancellation of both actively running and future scheduled downloads.
        *   **`receive_waiting_room`, `receive_stream_notification`**: Callbacks for handling external events from the `pikl_api`, such as a YouTube waiting room being detected or a stream going live.

*   `pikl_api/`:
    *   Handles integration with an external "Pikl API", likely a custom service for managing waiting rooms or notifications for YouTube channels.
    *   `waiting_room_client.py`: Provides client functionality to interact with the `pikl_api`, including subscribing/unsubscribing to channels and managing waiting room events.

*   `repositories/`:
    *   This layer abstracts database access, providing methods for interacting with specific data entities.
    *   `download_repository.py`:
        *   Manages database operations related to downloads.
        *   Stores and retrieves information about `completion_channels` (where download notifications should be sent).
        *   Handles `future_downloads`, including adding, getting, deleting, and marking them as invalid.
        *   Manages `subscribed_waiting_room` entries.
    *   `subscription_repository.py`:
        *   Manages database operations related to channel subscriptions.
        *   Stores which Discord guilds and channels are subscribed to specific YouTube channels for different `RoomKind` (e.g., streams, videos).

*   `services/`:
    *   This layer contains business logic and orchestrates operations, often using repositories.
    *   `notification_service.py`:
        *   `DiscordNotificationService`: Handles sending notifications back to Discord channels, typically after a download starts or completes.

## Configuration

The bot uses a `config` object (likely loaded from environment variables or a configuration file) to manage settings such as:
*   `log_level`
*   `database_file`
*   `discord_key`
*   `pikl_url` (for optional `pikl_api` integration)
*   `yt_dlp_config` (parameters for `yt-dlp`)
*   `streamlink_config` (parameters for `streamlink`)
*   `polling_interval_s` (for background tasks)

## Running the Bot

The bot is started by executing `main.py`. It runs as an asynchronous application, processing Discord commands and managing background download tasks. If the `pikl_api` is configured, it also runs an asynchronous client to interact with that service.
