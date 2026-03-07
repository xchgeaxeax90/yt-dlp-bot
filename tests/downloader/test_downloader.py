import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import datetime
from yt_dlp_bot.downloader.downloader import Downloader, AvailableNow, AvailableFuture, AvailabilityError

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

@pytest.mark.asyncio
async def test_download_records_file(downloader):
    url = "http://example.com/video"
    filename = "/path/to/video.mp4"
    event = MagicMock()
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        instance.extract_info.return_value = {'title': 'video'}
        instance.prepare_filename.return_value = filename
        
        await downloader._download(url, notify=False, extra_args={}, event=event)
        
        downloader.download_repository.add_downloaded_file.assert_called_once_with(url, filename)
        downloader.download_repository.delete_completion_for_url.assert_called_once_with(url)

@pytest.mark.asyncio
async def test_download_streamlink_records_file(downloader):
    url = "http://example.com/stream"
    downloader.get_info = MagicMock(return_value={'title': 'stream', 'id': 'vid1'})
    
    # Mock subprocess execution for streamlink and ffmpeg
    with patch('asyncio.create_subprocess_exec') as mock_exec, \
         patch('os.remove') as mock_remove:
        
        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        await downloader._download_streamlink(url, notify=False, event=MagicMock())
        
        # Should be called twice: once for streamlink, once for ffmpeg
        assert mock_exec.call_count == 2
        
        # Check if add_downloaded_file was called
        # The filename has a timestamp, so we check using ANY or regex
        args, kwargs = downloader.download_repository.add_downloaded_file.call_args
        assert args[0] == url
        assert "stream_vid1_" in args[1]
        assert args[1].endswith(".mp4")
        
        downloader.download_repository.delete_completion_for_url.assert_called_once_with(url)
