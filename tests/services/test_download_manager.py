import pytest
import asyncio
import threading
import datetime
import os
from unittest.mock import MagicMock, patch, AsyncMock
from yt_dlp_bot.services.download_manager import DownloadManager, DownloadTask

@pytest.fixture
def mock_downloader():
    return MagicMock()

@pytest.fixture
def mock_repo():
    m = MagicMock()
    m.get_completion_channel_for_url.return_value = None
    return m

@pytest.fixture
def mock_notif():
    return AsyncMock()

@pytest.fixture
def download_manager(mock_downloader, mock_repo, mock_notif):
    return DownloadManager(mock_downloader, mock_repo, mock_notif)

@pytest.mark.asyncio
async def test_start_download_adds_to_repo_and_tasks(download_manager, mock_repo):
    with patch.object(download_manager, 'create_download_task') as mock_create:
        mock_task = MagicMock(spec=DownloadTask)
        mock_create.return_value = mock_task
        
        await download_manager.start_download("http://url", 123, 456)
        
        mock_repo.add_completion_for_url.assert_called_once_with(123, 456, "http://url")
        mock_create.assert_called_once_with("http://url", False, {}, False)
        assert download_manager.current_downloads["http://url"] == mock_task

def test_cancel_download_success(download_manager):
    mock_task = MagicMock(spec=DownloadTask)
    mock_task.event = MagicMock(spec=threading.Event)
    download_manager.current_downloads["http://url"] = mock_task
    
    result = download_manager.cancel_download("http://url")
    assert result is True
    mock_task.event.set.assert_called_once()

def test_cancel_download_not_running(download_manager):
    result = download_manager.cancel_download("http://url")
    assert result is False

@pytest.mark.asyncio
async def test_notify_for_download(download_manager, mock_repo, mock_notif):
    mock_repo.get_completion_channel_for_url.return_value = (123, 456)
    
    await download_manager._notify_for_download("http://url", "message")
    
    mock_notif.notify.assert_called_once_with(123, 456, "message")

@pytest.mark.asyncio
async def test_download_records_file(download_manager, mock_repo):
    url = "http://example.com/video"
    filename = "/path/to/video.mp4"
    event = MagicMock()
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        instance.extract_info.return_value = {'title': 'video'}
        instance.prepare_filename.return_value = filename
        
        await download_manager._download(url, notify=False, extra_args={}, event=event)
        
        mock_repo.add_downloaded_file.assert_called_once_with(url, filename)
        mock_repo.delete_completion_for_url.assert_called_once_with(url)

@pytest.mark.asyncio
async def test_download_streamlink_records_file(download_manager, mock_downloader, mock_repo):
    url = "http://example.com/stream"
    mock_downloader.get_info = MagicMock(return_value={'title': 'stream', 'id': 'vid1'})
    
    # Mock subprocess execution for streamlink and ffmpeg
    with patch('asyncio.create_subprocess_exec') as mock_exec, \
         patch('os.remove') as mock_remove:
        
        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        await download_manager._download_streamlink(url, notify=False, event=MagicMock())
        
        # Should be called twice: once for streamlink, once for ffmpeg
        assert mock_exec.call_count == 2
        
        # Check if add_downloaded_file was called
        args, kwargs = mock_repo.add_downloaded_file.call_args
        assert args[0] == url
        assert "stream_vid1_" in args[1]
        assert args[1].endswith(".mp4")
        
        mock_repo.delete_completion_for_url.assert_called_once_with(url)
