import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from yt_dlp_bot.cogs.system import System, DownloadedFileListView
from yt_dlp_bot.helpers import Config
import os
import discord

@pytest.fixture
def mock_bot():
    return AsyncMock()

@pytest.fixture
def mock_download_repository():
    return MagicMock()

@pytest.fixture
def mock_config():
    config = Config()
    config.yt_dlp_config = {'paths': {'home': '/test/download/path'}}
    return config

@pytest.fixture
def system_cog(mock_bot, mock_download_repository, mock_config):
    return System(mock_bot, mock_download_repository, mock_config)

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    return ctx

@pytest.mark.asyncio
async def test_df_command(system_cog, mock_ctx, mocker):
    mocker.patch("shutil.disk_usage", return_value=MagicMock(free=2 * (1024**3))) # 2 GiB free
    await system_cog.df.callback(system_cog, mock_ctx)
    mock_ctx.send.assert_called_once_with("Free space 2.0 GiB")

@pytest.mark.asyncio
async def test_list_files_empty(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_files.return_value = []
    await system_cog.list_files.callback(system_cog, mock_ctx)
    mock_ctx.send.assert_called_once_with("No tracked downloaded files.")

@pytest.mark.asyncio
async def test_list_files_not_empty(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_files.return_value = [
        (1, "http://url1", "/path/to/very_long_filename_that_should_be_truncated_at_some_point.mp4", "2025-01-01 12:00:00", None)
    ]
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024 * 1024 * 5): # 5 MiB
        await system_cog.list_files.callback(system_cog, mock_ctx)
        
        mock_ctx.send.assert_called_once()
        args, kwargs = mock_ctx.send.call_args
        
        # Check that an embed and view were sent
        assert "embed" in kwargs
        assert "view" in kwargs
        embed = kwargs["embed"]
        assert "Tracked Downloaded Files" in embed.title
        assert "very_long_filename_that_should_be_tru..." in embed.description
        assert "5.0 MiB" in embed.description

@pytest.mark.asyncio
async def test_delete_file_success(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_file_by_id.return_value = ("/path/to/file1.mp4",)
    
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, 1)
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        mock_download_repository.delete_downloaded_file.assert_called_once_with(1)
        mock_ctx.send.assert_called_once_with("Deleted file from disk and record 1 from database.")

@pytest.mark.asyncio
async def test_delete_file_not_found_on_disk(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_file_by_id.return_value = ("/path/to/file1.mp4",)
    
    with patch("os.path.exists", return_value=False):
        await system_cog.delete_file.callback(system_cog, mock_ctx, 1)
        
        mock_download_repository.delete_downloaded_file.assert_called_once_with(1)
        mock_ctx.send.assert_called_once_with("File not found on disk, but record 1 was removed from database.")

@pytest.mark.asyncio
async def test_delete_file_not_in_db(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_file_by_id.return_value = None
    
    await system_cog.delete_file.callback(system_cog, mock_ctx, 1)
    mock_ctx.send.assert_called_once_with("No file found with ID 1")
