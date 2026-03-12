import sqlite3
from ..database import YoutubeWaitingRoom

class DownloadRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def add_completion_for_url(self, guild_id: int, channel_id: int, url: str):
        with self.con:
            self.con.execute("""INSERT OR IGNORE INTO completion_channels(guild_id, channel_id, url)
            VALUES (?, ?, ?)""", (guild_id, channel_id, url))

    def get_completion_channel_for_url(self, url: str):
        return self.con.execute("""SELECT guild_id, channel_id FROM completion_channels
            WHERE url = ?;""", (url, )).fetchone()

    def delete_completion_for_url(self, url: str):
        with self.con:
            return self.con.execute("""DELETE FROM completion_channels
            WHERE url = ?;""", (url, ))

    def add_future_download(self, url: str, utcepoch: int):
        with self.con:
            self.con.execute("""INSERT INTO future_downloads(url, utcepoch, valid)
            VALUES (?, ?, 1)
            ON CONFLICT(url)
            DO UPDATE SET utcepoch=excluded.utcepoch, valid=excluded.valid""", (url, utcepoch))


    def cleanup_future_downloads(self):
        with self.con:
            self.con.execute("""DELETE FROM future_downloads WHERE
            (utcepoch - unixepoch()) < -86400;""")


    def get_downloads_now(self, time_offset: int):
        result = self.con.execute("""SELECT url FROM future_downloads WHERE utcepoch < (unixepoch() + ?) AND valid <> 0;""",
                         (time_offset, )).fetchall()
        return [r[0] for r in result]

    def delete_future_download(self, url: str):
        with self.con:
            self.con.execute("""DELETE FROM future_downloads WHERE url=?""",
                             (url,))

    def add_downloaded_file(self, url: str, filepath: str):
        with self.con:
            self.con.execute("""INSERT INTO downloaded_files(url, filepath)
            VALUES (?, ?)""", (url, filepath))

    def get_downloaded_files(self):
        results = self.con.execute("""SELECT id, url, filepath, download_time, is_public, last_check FROM downloaded_files ORDER BY download_time DESC;""").fetchall()
        return results

    def get_downloaded_files_for_scan(self, time_delta):
        if time_delta:
            # We expect time_delta to be a timedelta object; convert to total seconds for SQLite.
            seconds = time_delta.total_seconds()
            return self.con.execute("""SELECT id, url FROM downloaded_files
                                       WHERE (is_public IS NULL)
                                       OR (is_public = 1 AND last_check < (unixepoch() - ?))""",
                                    (seconds,)).fetchall()
        else:
            return self.con.execute("""SELECT id, url FROM downloaded_files WHERE is_public IS NULL""").fetchall()


    def get_downloaded_file_by_id(self, file_id: int):
        return self.con.execute("""SELECT filepath FROM downloaded_files
            WHERE id = ?;""", (file_id, )).fetchone()

    def delete_downloaded_file(self, file_id: int):
        with self.con:
            self.con.execute("""DELETE FROM downloaded_files
            WHERE id = ?;""", (file_id, ))

    def update_downloaded_file_status(self, file_id: int, is_public: int):
        with self.con:
            self.con.execute("""UPDATE downloaded_files
                                SET is_public = ?, last_check = unixepoch()
                                WHERE id = ?""", (is_public, file_id))


    def disable_future_download(self, url: str):
        with self.con:
            self.con.execute("""UPDATE future_downloads SET valid=0 WHERE url=?""",
                             (url,))

    def get_all_scheduled_downloads(self):
        results = self.con.execute("""SELECT url, utcepoch FROM future_downloads WHERE valid <> 0 ORDER BY utcepoch ASC;""").fetchall()
        return results

    def add_subscribed_waiting_room(self, room: YoutubeWaitingRoom, url: str):
        with self.con:
            cursor = self.con.cursor()
            cursor.execute("""INSERT OR IGNORE INTO future_downloads (url, utcepoch)
                SELECT ?, ?
                WHERE EXISTS (
                    SELECT 1 FROM subscribed_channels WHERE youtube_channel = ? AND room_kind = ?
            );""", (url, room.utcepoch, room.channel_id.lower(), room.kind.value))
            return cursor.lastrowid != 0
