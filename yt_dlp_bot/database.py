import sqlite3
from collections import defaultdict
from itertools import groupby
from yt_dlp_bot.helpers import config
from dataclasses import dataclass
from pydantic import BaseModel
import datetime
from enum import Enum

class RoomKind(Enum):
    STREAM = 'streams'
    PREMIERE = 'videos'

class YoutubeVideo(BaseModel):
    channel_id: str
    video_id: str
    @property
    def url(self):
        return f"https://youtube.com/watch?v={self.video_id}"

class YoutubeWaitingRoom(YoutubeVideo):
    title: str
    kind: RoomKind
    utcepoch: int

    @property
    def utcdatetime(self):
        return datetime.datetime.fromtimestamp(self.utcepoch).astimezone(datetime.timezone.utc)

class Database:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
        #self.con.isolation_level = None
        self.cursor = self.con.cursor()
        self.setup_tables()

    def setup_tables(self):
        with self.con:
            self.con.execute("""CREATE TABLE IF NOT EXISTS completion_channels (
            guild_id integer, channel_id integer, url text,
            UNIQUE(guild_id, channel_id, url));""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS future_downloads (
            url text, utcepoch int, valid int DEFAULT 1, UNIQUE(url)
            );""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS subscribed_channels (
                guild_id integer, channel_id integer, youtube_channel text, room_kind text, UNIQUE(guild_id, youtube_channel, room_kind));""")

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

    def subscribe_to_channel(self, youtube_channel: str, kind: RoomKind, guild_id: int, channel_id: int):
        with self.con:
            self.con.execute("""INSERT OR IGNORE INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id)
                 VALUES (?, ?, ?, ?)""", (youtube_channel.lower(), kind.value if kind else None, guild_id, channel_id))

    def unsubscribe_from_channel(self, youtube_channel: str, kind: RoomKind | None, guild_id: int):
        if kind:
            with self.con:
                self.con.execute("""DELETE FROM subscribed_channels
                WHERE youtube_channel = ? AND room_kind = ? AND guild_id = ?;""", (youtube_channel.lower(), kind.value, guild_id))
        else:
            with self.con:
                self.con.execute("""DELETE FROM subscribed_channels
                WHERE youtube_channel = ? AND guild_id = ?;""", (youtube_channel.lower(), guild_id))

    def get_guild_info_for_subscription(self, youtube_channel: str, kind: RoomKind):
        return self.con.execute("""SELECT guild_id, channel_id FROM subscribed_channels
            WHERE youtube_channel = ? AND room_kind = ?""",
            (youtube_channel, kind.value)).fetchall()

db = Database(config.database_file)
