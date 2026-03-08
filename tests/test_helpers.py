import pytest
from datetime import timedelta, datetime, timezone
from yt_dlp_bot.services.download_service import parse_text_duration_timedelta, DownloadService
from unittest.mock import MagicMock

def test_parse_text_duration_timedelta():
    assert parse_text_duration_timedelta("1d") == timedelta(days=1)
    assert parse_text_duration_timedelta("2h") == timedelta(hours=2)
    assert parse_text_duration_timedelta("30m") == timedelta(minutes=30)
    assert parse_text_duration_timedelta("45s") == timedelta(seconds=45)
    assert parse_text_duration_timedelta("1d2h3m4s") == timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert parse_text_duration_timedelta("invalid") is None

def test_parse_text_as_datetime_discord_format():
    # We need a download service instance because it's a method
    ds = DownloadService(MagicMock(), MagicMock(), MagicMock())
    ts = 123456789
    result = ds.parse_text_as_datetime(f"<t:{ts}:F>")
    assert result.timestamp() == pytest.approx(ts)
