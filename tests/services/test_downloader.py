import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import datetime
from yt_dlp_bot.services.downloader import Downloader, AvailableNow, AvailableFuture, AvailabilityError

@pytest.fixture
def downloader():
    repo = MagicMock()
    repo.get_completion_channel_for_url.return_value = None
    sub_repo = MagicMock()
    notif = MagicMock()
    return Downloader(repo, sub_repo, notif)

@pytest.mark.asyncio
async def test_get_availability_now(downloader):
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        instance.extract_info.return_value = {'live_status': 'is_live'}
        
        result = await downloader.get_availability("http://url")
        assert isinstance(result, AvailableNow)

@pytest.mark.asyncio
async def test_get_availability_future(downloader):
    future_ts = int(datetime.datetime.now().timestamp() + 3600)
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        instance.extract_info.return_value = {
            'live_status': 'is_upcoming',
            'release_timestamp': future_ts
        }
        
        result = await downloader.get_availability("http://url")
        assert isinstance(result, AvailableFuture)
        assert result.epoch.timestamp() == pytest.approx(future_ts)

@pytest.mark.asyncio
async def test_get_availability_error(downloader):
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        instance.extract_info.side_effect = Exception("Some error")
        
        result = await downloader.get_availability("http://url")
        assert isinstance(result, AvailabilityError)
        assert "Some error" in result.errorstr

def test_defer_download_until_time(downloader):
    time = datetime.datetime.now(datetime.timezone.utc)
    downloader.defer_download_until_time("http://url", time, 123, 456)
    
    downloader.download_repository.add_future_download.assert_called_once_with("http://url", int(time.timestamp()))
    downloader.download_repository.add_completion_for_url.assert_called_once_with(123, 456, "http://url")

def test_cancel_scheduled_download(downloader):
    downloader.download_repository.get_all_scheduled_downloads.return_value = [("http://url", 1000)]
    
    result = downloader.cancel_scheduled_download("http://url")
    assert result is True
    downloader.download_repository.disable_future_download.assert_called_once_with("http://url")

def test_cancel_scheduled_download_not_found(downloader):
    downloader.download_repository.get_all_scheduled_downloads.return_value = [("http://other", 1000)]
    
    result = downloader.cancel_scheduled_download("http://url")
    assert result is False
