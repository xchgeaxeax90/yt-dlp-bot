# Discord Bot Commands

This document outlines the commands available for the Discord bot. The default prefix is `y?`.

## YtDl Commands

### `download <url>`
*   **Brief**: Downloads a video or stream asynchronously.
*   **Description**: Downloads a video immediately or schedules it if it's an upcoming live stream.
*   **Usage**: `y?download <url>`

### `scheduled-download <url> <timestamp>`
*   **Brief**: Forces a video download at a specific time.
*   **Description**: Schedules a download for a specific time (e.g., `<t:12345678:F>` or `1h`).
*   **Usage**: `y?scheduled-download <url> <timestamp>`

### `streamlink-download <url>`
*   **Brief**: Forces a video download through streamlink.
*   **Usage**: `y?streamlink-download <url>`

### `get-running-downloads`
*   **Brief**: Gets the currently running downloads.
*   **Usage**: `y?get-running-downloads`

### `get-scheduled-downloads`
*   **Brief**: Gets the currently scheduled downloads.
*   **Usage**: `y?get-scheduled-downloads`

### `cancel <url>`
*   **Brief**: Cancels a running or scheduled download.
*   **Usage**: `y?cancel <url>`

## Subscription Commands

### `subscription subscribe <youtube_channel> <kind>`
*   **Brief**: Subscribes to automatic downloads for a channel.
*   **Description**: `kind` can be `streams` or `videos`.
*   **Usage**: `y?subscription subscribe <youtube_channel> <kind>`

### `subscription unsubscribe <youtube_channel> [kind]`
*   **Brief**: Unsubscribes from automatic downloads for a channel.
*   **Usage**: `y?subscription unsubscribe <youtube_channel> [kind]`

### `subscription list`
*   **Brief**: Lists current subscriptions for the guild.
*   **Usage**: `y?subscription list`

## System Commands (Owner Only)

### `system df`
*   **Brief**: Gets disk usage of the download directory.
*   **Usage**: `y?system df`

### `system list`
*   **Brief**: List all tracked downloaded files.
*   **Description**: Displays a paginated list of files with IDs, truncated names, and sizes.
*   **Usage**: `y?system list`

### `system delete <id>`
*   **Brief**: Deletes a tracked file by ID.
*   **Description**: Removes the file from disk and the record from the database.
*   **Usage**: `y?system delete <id>`

### `system purge`
*   **Brief**: Purges database records for missing files.
*   **Description**: Checks all records and removes those where the file is no longer on disk.
*   **Usage**: `y?system purge`

### `system scan [include_public] [older_than]`
*   **Brief**: Scans tracked files for availability using `yt-dlp`.
*   **Description**:
    *   `include_public`: (bool) If True, also scans files already marked as public.
    *   `older_than`: (string) e.g., `1w`, `2d`. Only scans files checked longer ago than this.
*   **Usage**: `y?system scan True 1w`

## Sync Commands

### `sync`
*   **Brief**: Synchronizes the bot's application commands with Discord.
*   **Usage**: `y?sync`
