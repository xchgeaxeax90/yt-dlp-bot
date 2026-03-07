import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import datetime
from yt_dlp_bot.downloader.downloader import Downloader, AvailableNow, AvailableFuture, AvailabilityError

@pytest.fixture
def downloader():
    repo = MagicMock()
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
