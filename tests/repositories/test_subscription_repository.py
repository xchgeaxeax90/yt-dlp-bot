import sqlite3
import pytest
from yt_dlp_bot.repositories.subscription_repository import SubscriptionRepository
from yt_dlp_bot.database import RoomKind

@pytest.fixture
def sub_repo(db_conn: sqlite3.Connection):
    return SubscriptionRepository(db_conn)

def test_subscribe_to_channel(sub_repo, db_conn):
    sub_repo.subscribe_to_channel("Chan1", RoomKind.STREAM, 123, 456)
    
    cursor = db_conn.execute("SELECT youtube_channel, room_kind, guild_id, channel_id FROM subscribed_channels")
    row = cursor.fetchone()
    # Note: Case normalization in repository
    assert row == ("chan1", "streams", 123, 456)

def test_subscribe_to_channel_ignore_duplicate(sub_repo, db_conn):
    sub_repo.subscribe_to_channel("chan1", RoomKind.STREAM, 1, 1)
    sub_repo.subscribe_to_channel("chan1", RoomKind.STREAM, 1, 1)
    
    cursor = db_conn.execute("SELECT count(*) FROM subscribed_channels")
    assert cursor.fetchone()[0] == 1

def test_unsubscribe_from_channel_specific_kind(sub_repo, db_conn):
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "streams", 1, 1))
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "videos", 1, 1))
    
    sub_repo.unsubscribe_from_channel("chan1", RoomKind.STREAM, 1)
    
    cursor = db_conn.execute("SELECT room_kind FROM subscribed_channels WHERE youtube_channel='chan1'").fetchall()
    kinds = [r[0] for r in cursor]
    assert "streams" not in kinds
    assert "videos" in kinds

def test_unsubscribe_from_all_kinds(sub_repo, db_conn):
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "streams", 1, 1))
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "videos", 1, 1))
    
    sub_repo.unsubscribe_from_channel("chan1", None, 1)
    
    cursor = db_conn.execute("SELECT count(*) FROM subscribed_channels WHERE youtube_channel='chan1'")
    assert cursor.fetchone()[0] == 0

def test_get_guild_info_for_subscription(sub_repo, db_conn):
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "streams", 123, 456))
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "streams", 789, 101))
    
    results = sub_repo.get_guild_info_for_subscription("chan1", RoomKind.STREAM)
    assert set(results) == {(123, 456), (789, 101)}

def test_get_subscriptions(sub_repo, db_conn):
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan1", "streams", 123, 456))
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan2", "videos", 123, 789))
    db_conn.execute("INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) VALUES (?, ?, ?, ?)",
                    ("chan3", "streams", 456, 111))
    
    results = sub_repo.get_subscriptions(123)
    expected = [(123, 456, "chan1", "streams"), (123, 789, "chan2", "videos")]
    assert set(results) == set(expected)
