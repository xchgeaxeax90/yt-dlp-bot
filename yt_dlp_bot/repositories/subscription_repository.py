import sqlite3
from ..database import RoomKind

class SubscriptionRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

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

    def get_subscriptions(self, guild_id: int):
        return self.con.execute("""SELECT guild_id, channel_id, youtube_channel, room_kind FROM subscribed_channels
            WHERE guild_id = ?""", (guild_id,)).fetchall()
