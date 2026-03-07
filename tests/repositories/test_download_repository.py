import sqlite3
import pytest
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.database import YoutubeWaitingRoom, RoomKind

@pytest.fixture
def download_repo(db_conn: sqlite3.Connection):
    return DownloadRepository(db_conn)

def test_add_and_get_completion_for_url(download_repo):
    download_repo.add_completion_for_url(123, 456, "http://example.com")
    result = download_repo.get_completion_channel_for_url("http://example.com")
    assert result == (123, 456)

def test_delete_completion_for_url(download_repo):
    download_repo.add_completion_for_url(123, 456, "http://example.com")
    download_repo.delete_completion_for_url("http://example.com")
    result = download_repo.get_completion_channel_for_url("http://example.com")
    assert result is None

def test_add_future_download(download_repo, db_conn):
    url = "http://example.com/future"
    utcepoch = 2000000000
    download_repo.add_future_download(url, utcepoch)
    
    cursor = db_conn.execute("SELECT utcepoch, valid FROM future_downloads WHERE url=?", (url,))
    row = cursor.fetchone()
    assert row == (utcepoch, 1)

def test_add_future_download_on_conflict(download_repo, db_conn):
    url = "http://example.com/future"
    download_repo.add_future_download(url, 1000)
    download_repo.add_future_download(url, 2000)
    
    cursor = db_conn.execute("SELECT utcepoch FROM future_downloads WHERE url=?", (url,))
    assert cursor.fetchone()[0] == 2000

def test_cleanup_future_downloads(download_repo, db_conn):
    # Old download (> 86400 seconds ago)
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch) VALUES (?, unixepoch() - 100000)", ("old",))
    # Recent download
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch) VALUES (?, unixepoch() - 1000)", ("recent",))
    
    download_repo.cleanup_future_downloads()
    
    cursor = db_conn.execute("SELECT url FROM future_downloads").fetchall()
    urls = [r[0] for r in cursor]
    assert "old" not in urls
    assert "recent" in urls

def test_get_downloads_now(download_repo, db_conn):
    # Now is 1000, threshold is 100
    # Download at 1050 should be picked up (1050 < 1000 + 100)
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch) VALUES (?, unixepoch() + 50)", ("nowish",))
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch) VALUES (?, unixepoch() + 150)", ("later",))
    
    results = download_repo.get_downloads_now(100)
    assert "nowish" in results
    assert "later" not in results

def test_add_subscribed_waiting_room_when_subscribed(download_repo, db_conn):
    # Setup subscription
    db_conn.execute("""INSERT INTO subscribed_channels (youtube_channel, room_kind, guild_id, channel_id) 
                       VALUES (?, ?, ?, ?)""", ("chan1", "streams", 1, 1))
    
    room = YoutubeWaitingRoom(channel_id="chan1", video_id="vid1", title="test", kind=RoomKind.STREAM, utcepoch=3000)
    added = download_repo.add_subscribed_waiting_room(room, room.url)
    
    assert added is True
    cursor = db_conn.execute("SELECT url FROM future_downloads WHERE url=?", (room.url,))
    assert cursor.fetchone() is not None

def test_add_subscribed_waiting_room_when_not_subscribed(download_repo, db_conn):
    room = YoutubeWaitingRoom(channel_id="chan1", video_id="vid1", title="test", kind=RoomKind.STREAM, utcepoch=3000)
    added = download_repo.add_subscribed_waiting_room(room, room.url)
    
    assert added is False
    cursor = db_conn.execute("SELECT url FROM future_downloads WHERE url=?", (room.url,))
    assert cursor.fetchone() is None

def test_delete_future_download(download_repo, db_conn):
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch) VALUES (?, ?)", ("http://example.com/delete", 1000))
    download_repo.delete_future_download("http://example.com/delete")
    cursor = db_conn.execute("SELECT COUNT(*) FROM future_downloads WHERE url=?", ("http://example.com/delete",))
    assert cursor.fetchone()[0] == 0

def test_disable_future_download(download_repo, db_conn):
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch, valid) VALUES (?, ?, 1)", ("http://example.com/disable", 1000))
    download_repo.disable_future_download("http://example.com/disable")
    cursor = db_conn.execute("SELECT valid FROM future_downloads WHERE url=?", ("http://example.com/disable",))
    assert cursor.fetchone()[0] == 0

def test_get_all_scheduled_downloads(download_repo, db_conn):
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch, valid) VALUES (?, ?, 1)", ("url1", 2000))
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch, valid) VALUES (?, ?, 1)", ("url2", 1000))
    db_conn.execute("INSERT INTO future_downloads (url, utcepoch, valid) VALUES (?, ?, 0)", ("url3", 3000)) # Invalid
    
    results = download_repo.get_all_scheduled_downloads()
    expected = [("url2", 1000), ("url1", 2000)] # Ordered by utcepoch ASC
    assert results == expected
