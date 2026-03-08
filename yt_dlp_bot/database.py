import sqlite3
from pydantic import BaseModel
import datetime
from enum import Enum

class RoomKind(Enum):
    STREAM = 'streams'
    PREMIERE = 'videos'

class SubscriptionModel(BaseModel):
    guild_id: int
    channel_id: int
    youtube_channel: str
    kind: RoomKind

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

def init_database(db_name: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_name)
    _setup_tables(con)
    return con

def _setup_tables(con: sqlite3.Connection):
    with con:
        con.execute("""CREATE TABLE IF NOT EXISTS completion_channels (
        guild_id integer, channel_id integer, url text,
        UNIQUE(guild_id, channel_id, url));""")
        con.execute("""CREATE TABLE IF NOT EXISTS future_downloads (
        url text, utcepoch int, valid int DEFAULT 1, UNIQUE(url)
        );""")
        con.execute("""CREATE TABLE IF NOT EXISTS subscribed_channels (
            guild_id integer, channel_id integer, youtube_channel text, room_kind text, UNIQUE(guild_id, youtube_channel, room_kind));""")
        con.execute("""CREATE TABLE IF NOT EXISTS downloaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            filepath TEXT,
            download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_public INTEGER,
            last_check TIMESTAMP
        );""")

