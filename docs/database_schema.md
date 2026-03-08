# Database Schema

This document describes the SQLite database schema used by the `yt-dlp-bot` project. The database is initialized and tables are created by the `_setup_tables` function in `yt_dlp_bot/database.py`.

## Tables

### `completion_channels`

This table stores information about which Discord channels should receive notifications upon the completion of a specific download URL.

| Column       | Type    | Description                                       |
| :----------- | :------ | :------------------------------------------------ |
| `guild_id`   | `integer` | The unique ID of the Discord guild.               |
| `channel_id` | `integer` | The unique ID of the Discord channel within the guild. |
| `url`        | `text`  | The URL of the content that was downloaded or is being downloaded. |

**Constraints:**
*   `UNIQUE(guild_id, channel_id, url)`: Ensures that a specific Discord channel in a guild is registered to receive completion notifications for a given URL only once.

### `future_downloads`

This table manages downloads that are scheduled to occur at a future time.

| Column       | Type      | Description                                       |
| :----------- | :-------- | :------------------------------------------------ |
| `url`        | `text`    | The URL of the content scheduled for future download. |
| `utcepoch`   | `integer` | A UTC epoch timestamp indicating when the download is scheduled to become available or be processed. |
| `valid`      | `integer` | A flag (1 for valid, 0 for invalid/disabled) indicating if the scheduled download is still active. Defaults to `1`. |

**Constraints:**
*   `UNIQUE(url)`: Ensures that each URL can only be scheduled once in this table.

### `subscribed_channels`

This table tracks Discord guilds and channels that are subscribed to specific YouTube channels for automatic content downloads (e.g., streams or videos).

| Column            | Type      | Description                                       |
| :---------------- | :-------- | :------------------------------------------------ |
| `guild_id`        | `integer` | The unique ID of the Discord guild.               |
| `channel_id`      | `integer` | The unique ID of the Discord channel where the subscription was made. |
| `youtube_channel` | `text`    | The identifier (ID or name) of the YouTube channel being subscribed to. |
| `room_kind`       | `text`    | The type of content from the YouTube channel being subscribed to. This corresponds to the `RoomKind` enum (e.g., `'streams'`, `'videos'`). |

**Constraints:**
*   `UNIQUE(guild_id, youtube_channel, room_kind)`: Ensures that a specific Discord guild cannot subscribe to the same kind of content from a particular YouTube channel multiple times.

### `downloaded_files`

This table tracks successfully completed downloads.

| Column          | Type      | Description                                       |
| :-------------- | :-------- | :------------------------------------------------ |
| `id`            | `integer` | Primary key (autoincrement).                       |
| `url`           | `text`    | The source URL of the video.                      |
| `filepath`      | `text`    | The path to the downloaded file on disk.          |
| `download_time` | `timestamp`| The time when the download was completed.         |
| `is_public`     | `integer` | 1 if the video is public, 0 if private/deleted, NULL if unknown. |
| `last_check`    | `timestamp`| The last time the availability of the URL was checked. |
