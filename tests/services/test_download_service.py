import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
from yt_dlp_bot.services.download_service import DownloadService
from yt_dlp_bot.downloader.downloader import AvailableNow, AvailableFuture, AvailabilityError

@pytest.fixture
def mock_downloader():
    m = MagicMock()
    m.get_availability = AsyncMock()
    return m

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_manager():
    m = MagicMock()
    m.start_download = AsyncMock()
    return m

@pytest.fixture
def download_service(mock_downloader, mock_repo, mock_manager):
    return DownloadService(mock_downloader, mock_repo, mock_manager)

def test_parse_text_as_datetime_discord_timestamp(download_service):
    # <t:123456789:F>
    result = download_service.parse_text_as_datetime("<t:123456789:F>")
    expected = datetime.fromtimestamp(123456789).astimezone(timezone.utc)
    assert result == expected

def test_parse_text_as_datetime_duration(download_service):
    with patch('yt_dlp_bot.services.download_service.datetime') as mock_datetime:
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        # Duration 1d1h1m1s = 86400 + 3600 + 60 + 1 = 90061
        result = download_service.parse_text_as_datetime("1d1h1m1s")
        expected = now + timedelta(days=1, hours=1, minutes=1, seconds=1)
        assert result == expected

@pytest.mark.asyncio
async def test_initiate_download_streamlink(download_service, mock_manager):
    result = await download_service.initiate_download("http://url", 1, 1, streamlink=True)
    assert result == "Starting streamlink download"
    mock_manager.start_download.assert_called_once_with("http://url", 1, 1, streamlink=True)

@pytest.mark.asyncio
async def test_initiate_download_now(download_service, mock_downloader, mock_manager):
    mock_downloader.get_availability.return_value = AvailableNow()
    result = await download_service.initiate_download("http://url", 1, 1)
    assert result == "Downloading video now"
    mock_manager.start_download.assert_called_once_with("http://url", 1, 1)

@pytest.mark.asyncio
async def test_initiate_download_future(download_service, mock_downloader):
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_downloader.get_availability.return_value = AvailableFuture(future_time)
    
    with patch('discord.utils.format_dt', return_value="formatted_time"):
        result = await download_service.initiate_download("http://url", 1, 1)
        assert "Scheduling download for formatted_time" in result
        mock_downloader.defer_download_until_time.assert_called_once_with("http://url", future_time, 1, 1)

def test_schedule_download_success(download_service, mock_downloader):
    with patch('discord.utils.format_dt', return_value="formatted_time"):
        result = download_service.schedule_download("http://url", "1h", 1, 1)
        assert "Scheduling download for formatted_time" in result
        mock_downloader.defer_download_until_time.assert_called_once()

def test_schedule_download_invalid(download_service):
    result = download_service.schedule_download("http://url", "invalid", 1, 1)
    assert "Invalid timestamp format" in result

def test_cancel_download_running(download_service, mock_manager):
    mock_manager.cancel_download.return_value = True
    result = download_service.cancel_download("http://url")
    assert "Successfully cancelled running download" in result

def test_cancel_download_scheduled(download_service, mock_manager, mock_downloader):
    mock_manager.cancel_download.return_value = False
    mock_downloader.cancel_download.return_value = True
    result = download_service.cancel_download("http://url")
    assert "Successfully cancelled scheduled download" in result

def test_cancel_download_not_found(download_service, mock_manager, mock_downloader):
    mock_manager.cancel_download.return_value = False
    mock_downloader.cancel_download.return_value = False
    result = download_service.cancel_download("http://url")
    assert "Could not find" in result
