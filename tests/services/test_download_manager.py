import pytest
import asyncio
import threading
from unittest.mock import MagicMock, patch, AsyncMock
from yt_dlp_bot.services.download_manager import DownloadManager, DownloadTask

@pytest.fixture
def mock_downloader():
    return MagicMock()

@pytest.fixture
def mock_repo():
    return MagicMock()

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
