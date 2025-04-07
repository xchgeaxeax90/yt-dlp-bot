import sqlite3
from collections import defaultdict
from itertools import groupby
from bot.helpers import config

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
            url text, utcepoch int, UNIQUE(url)
            );""")

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
            self.con.execute("""INSERT OR IGNORE INTO future_downloads(url, utcepoch)
            VALUES (?, ?)""", (url, utcepoch))

    def get_downloads_now(self, time_offset: int):
        result = self.con.execute("""SELECT url FROM future_downloads WHERE utcepoch < (unixepoch() + ?);""",
                         (time_offset, )).fetchall()
        return [r[0] for r in result]

    def delete_future_download(self, url: str):
        with self.con:
            self.con.execute("""DELETE FROM future_downloads WHERE url = ?;""", (url,))

    def get_all_scheduled_downloads(self):
        results = self.con.execute("""SELECT url, utcepoch FROM future_downloads;""").fetchall()
        return results
        


db = Database(config.database_file)
