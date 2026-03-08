import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from yt_dlp_bot.services.scheduler_service import SchedulerService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_manager():
    return AsyncMock()

@pytest.fixture
def scheduler_service(mock_repo, mock_manager):
    # We need to mock config to avoid issues with polling_interval_s
    with patch('yt_dlp_bot.services.scheduler_service.config') as mock_config:
        mock_config.polling_interval_s = 60
        return SchedulerService(mock_repo, mock_manager)

@pytest.mark.asyncio
async def test_check_scheduled_downloads_no_urls(scheduler_service, mock_repo, mock_manager):
    mock_repo.get_downloads_now.return_value = []
    
    await scheduler_service._check_scheduled_downloads()
    
    mock_repo.get_downloads_now.assert_called_once()
    mock_manager.start_download.assert_not_called()
    mock_repo.cleanup_future_downloads.assert_called_once()

@pytest.mark.asyncio
async def test_check_scheduled_downloads_with_urls(scheduler_service, mock_repo, mock_manager):
    mock_repo.get_downloads_now.return_value = ["http://url1", "http://url2"]
    
    await scheduler_service._check_scheduled_downloads()
    
    mock_repo.get_downloads_now.assert_called_once()
    assert mock_manager.start_download.call_count == 2
    mock_repo.delete_future_download.assert_any_call("http://url1")
    mock_repo.delete_future_download.assert_any_call("http://url2")
    mock_repo.cleanup_future_downloads.assert_called_once()
