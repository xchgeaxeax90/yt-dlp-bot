# Discord Bot Commands

This document outlines the commands available for the Discord bot.

## YtDl Commands

### `download <url>`
*   **Brief**: Downloads a video or stream asynchronously
*   **Description**: Downloads a video or schedules a download in the future
*   **Usage**: `y!download https://www.youtube.com/watch?v=e6DSdJ9r-FM`

### `scheduled-download <url> <timestamp>`
*   **Brief**: Forces a video download at a specific time
*   **Description**: Forces a video download at a specific time
*   **Usage**: `y!scheduled-download <url> <timestamp>`

### `streamlink-download <url>`
*   **Brief**: Forces a video download through streamlink
*   **Description**: Forces a video download through streamlink
*   **Usage**: `y!streamlink-download <url>`

### `df`
*   **Brief**: Gets disk usage of the download directory
*   **Description**: Gets disk usage of the download directory
*   **Usage**: `y!df`

### `get-running-downloads`
*   **Brief**: Gets the currently running downloads
*   **Description**: Gets the currently running downloads
*   **Usage**: `y!get-running-downloads`

### `get-scheduled-downloads`
*   **Brief**: Gets the currently scheduled downloads
*   **Description**: Gets the currently scheduled downloads
*   **Usage**: `y!get-scheduled-downloads`

### `cancel <url>`
*   **Brief**: Cancels a download
*   **Description**: Cancels a download
*   **Usage**: `y!cancel <url>`

## Subscription Commands

### `subscription subscribe <youtube_channel> <kind>`
*   **Brief**: Subscribes to automatic downloads for a channel
*   **Description**: Subscribes to automatic downloads for a channel
*   **Usage**: `y!subscription subscribe <youtube_channel> <kind>`

### `subscription unsubscribe <youtube_channel> [kind]`
*   **Brief**: Unsubscribes from automatic downloads for a channel
*   **Description**: Unsubscribes from automatic downloads for a channel
*   **Usage**: `y!subscription unsubscribe <youtube_channel> [kind]`

## Sync Commands

### `sync`
*   **Brief**: Synchronizes the bot's application commands with discord
*   **Description**: Synchronizes the bot's application commands with discord
*   **Usage**: `t!sync`

### `restart`
*   **Brief**: Restarts the bot
*   **Description**: Restarts the bot
*   **Usage**: `t!restart`
