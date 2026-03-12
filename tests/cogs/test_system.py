import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from yt_dlp_bot.cogs.system import System, DownloadedFileListView
from yt_dlp_bot.helpers import Config
import os
import discord
import datetime

@pytest.fixture
def mock_bot():
    return AsyncMock()

@pytest.fixture
def mock_download_repository():
    return MagicMock()

@pytest.fixture
def mock_downloader():
    m = MagicMock()
    m.check_video_availability = AsyncMock()
    return m

@pytest.fixture
def mock_download_service():
    return MagicMock()

@pytest.fixture
def mock_config():
    config = Config()
    config.yt_dlp_config = {'paths': {'home': '/test/download/path'}}
    return config

@pytest.fixture
def system_cog(mock_bot, mock_download_repository, mock_downloader, mock_download_service, mock_config):
    return System(mock_bot, mock_download_repository, mock_downloader, mock_download_service, mock_config)

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
        (1, "http://url1", "/path/to/[3D] very_long_filename_that_should_be_truncated_at_some_point.mp4", "2025-01-01 12:00:00", 0, None) # is_public=0 (Private)
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
        # Check for filename (brackets removed) and ID
        assert "**ID: 1** | [3D very_long_filename_that_should_be_...](http://url1)" in embed.description
        assert " [Private]" in embed.description
        assert "5.0 MiB" in embed.description

@pytest.mark.asyncio
async def test_delete_file_success(system_cog, mock_ctx, mock_download_repository):
    # Mock return value as a tuple containing the filepath
    mock_download_repository.get_downloaded_file_by_id.return_value = ("/path/to/file1.mp4",)
    
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1")
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        mock_download_repository.delete_downloaded_file.assert_called_once_with(1)
        mock_ctx.send.assert_called_once_with("ID 1: Deleted from disk and DB.")

@pytest.mark.asyncio
async def test_delete_file_multiple(system_cog, mock_ctx, mock_download_repository):
    # Mock return values for multiple IDs
    mock_download_repository.get_downloaded_file_by_id.side_effect = [
        ("/path/to/file1.mp4",),
        None,
        ("/path/to/file3.mp4",)
    ]
    
    with patch("os.path.exists", side_effect=[True, False]), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1 2 3")
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        # delete_downloaded_file called for ID 1 and 3 (ID 3 not found on disk, but still deleted from DB)
        assert mock_download_repository.delete_downloaded_file.call_count == 2
        mock_download_repository.delete_downloaded_file.assert_any_call(1)
        mock_download_repository.delete_downloaded_file.assert_any_call(3)
        
        expected_output = "ID 1: Deleted from disk and DB.\nID 2: No file found.\nID 3: Not on disk, record removed from DB."
        mock_ctx.send.assert_called_once_with(expected_output)

@pytest.mark.asyncio
async def test_delete_file_not_found_on_disk(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_file_by_id.return_value = ("/path/to/file1.mp4",)
    
    with patch("os.path.exists", return_value=False):
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1")
        
        mock_download_repository.delete_downloaded_file.assert_called_once_with(1)
        mock_ctx.send.assert_called_once_with("ID 1: Not on disk, record removed from DB.")

@pytest.mark.asyncio
async def test_delete_file_not_in_db(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_file_by_id.return_value = None
    
    await system_cog.delete_file.callback(system_cog, mock_ctx, "1")
    mock_ctx.send.assert_called_once_with("ID 1: No file found.")

@pytest.mark.asyncio
async def test_delete_file_multiple_comma_separated(system_cog, mock_ctx, mock_download_repository):
    # Mock return values for multiple IDs
    mock_download_repository.get_downloaded_file_by_id.side_effect = [
        ("/path/to/file1.mp4",),
        None,
        ("/path/to/file3.mp4",)
    ]
    
    with patch("os.path.exists", side_effect=[True, False]), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1, 2,3")
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        assert mock_download_repository.delete_downloaded_file.call_count == 2
        
        expected_output = "ID 1: Deleted from disk and DB.\nID 2: No file found.\nID 3: Not on disk, record removed from DB."
        mock_ctx.send.assert_called_once_with(expected_output)

@pytest.mark.asyncio
async def test_delete_file_invalid_input(system_cog, mock_ctx, mock_download_repository):
    await system_cog.delete_file.callback(system_cog, mock_ctx, "1 abc 3")
    mock_ctx.send.assert_called_once_with("Please provide a valid list of integer IDs separated by spaces or commas.")

@pytest.mark.asyncio
async def test_delete_file_empty_input(system_cog, mock_ctx, mock_download_repository):
    await system_cog.delete_file.callback(system_cog, mock_ctx, "  ")
    mock_ctx.send.assert_called_once_with("Please provide at least one file ID.")

@pytest.mark.asyncio
async def test_purge_files(system_cog, mock_ctx, mock_download_repository):
    mock_download_repository.get_downloaded_files.return_value = [
        (1, "url1", "/path/exists", "time", None, None),
        (2, "url2", "/path/missing", "time", None, None)
    ]
    
    # Correctly mock side_effect for path exists check
    def exists_side_effect(path):
        return path == "/path/exists"

    with patch("os.path.exists", side_effect=exists_side_effect):
        await system_cog.purge_files.callback(system_cog, mock_ctx)
        
        mock_download_repository.delete_downloaded_file.assert_called_once_with(2)
        mock_ctx.send.assert_called_once_with("Purged 1 records from the database for missing files.")

@pytest.mark.asyncio
async def test_scan_files(system_cog, mock_ctx, mock_download_repository, mock_downloader):
    # Mock data: 1 public (scanned only if requested), 1 private (always scanned), 1 new (always scanned)
    mock_download_repository.get_downloaded_files.return_value = [
        (1, "url_pub", "/path1", "time", 1, None),
        (2, "url_priv", "/path2", "time", 0, None),
        (3, "url_new", "/path3", "time", None, None)
    ]
    
    mock_downloader.check_video_availability.side_effect = [False, True] # new results for ID 2 and 3
    
    # Run with default (don't include public)
    await system_cog.scan_files.callback(system_cog, mock_ctx, include_public=False)
    
    # Should scan ID 2 and 3
    assert mock_downloader.check_video_availability.call_count == 2
    mock_download_repository.update_downloaded_file_status.assert_any_call(2, 0, ANY)
    mock_download_repository.update_downloaded_file_status.assert_any_call(3, 1, ANY)
    
    # Verify summary message
    sent_msgs = [call.args[0] for call in mock_ctx.send.call_args_list]
    assert any("Scan complete. Scanned: 2, Still Public: 1, Now Private/Unavailable: 1" in m for m in sent_msgs)

@pytest.mark.asyncio
async def test_scan_files_include_public(system_cog, mock_ctx, mock_download_repository, mock_downloader):
    mock_download_repository.get_downloaded_files.return_value = [
        (1, "url_pub", "/path1", "time", 1, None)
    ]
    mock_downloader.check_video_availability.return_value = True
    
    await system_cog.scan_files.callback(system_cog, mock_ctx, include_public=True)
    
    mock_downloader.check_video_availability.assert_called_once_with("url_pub")
    mock_download_repository.update_downloaded_file_status.assert_called_once()

@pytest.mark.asyncio
async def test_scan_files_older_than(system_cog, mock_ctx, mock_download_repository, mock_downloader):
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = (now - datetime.timedelta(days=1)).isoformat()
    one_week_ago = (now - datetime.timedelta(days=7)).isoformat()
    
    mock_download_repository.get_downloaded_files.return_value = [
        (1, "recent", "/path1", "time", 0, one_day_ago),
        (2, "old", "/path2", "time", 0, one_week_ago)
    ]
    mock_downloader.check_video_availability.return_value = True
    
    # Mock parse_text_duration_timedelta since it's used in the command
    with patch("yt_dlp_bot.cogs.system.parse_text_duration_timedelta", return_value=datetime.timedelta(days=3)):
        await system_cog.scan_files.callback(system_cog, mock_ctx, include_public=False, older_than="3d")
    
    # Should only scan the one from a week ago
    mock_downloader.check_video_availability.assert_called_once_with("old")
    mock_download_repository.update_downloaded_file_status.assert_called_once_with(2, 1, ANY)
