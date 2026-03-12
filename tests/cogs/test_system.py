import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from yt_dlp_bot.cogs.system import System, DownloadedFileListView
from yt_dlp_bot.helpers import Config
from yt_dlp_bot.repositories.download_repository import DownloadRepository
import os
import discord
import datetime

@pytest.fixture
def mock_bot():
    return AsyncMock()

@pytest.fixture
def download_repository(db_conn):
    return DownloadRepository(db_conn)

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
def system_cog(mock_bot, download_repository, mock_downloader, mock_download_service, mock_config):
    return System(mock_bot, download_repository, mock_downloader, mock_download_service, mock_config)

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.defer = AsyncMock()
    return ctx

@pytest.mark.asyncio
async def test_df_command(system_cog, mock_ctx, mocker):
    mocker.patch("shutil.disk_usage", return_value=MagicMock(free=2 * (1024**3))) # 2 GiB free
    await system_cog.df.callback(system_cog, mock_ctx)
    mock_ctx.send.assert_called_once_with("Free space 2.0 GiB")

@pytest.mark.asyncio
async def test_list_files_empty(system_cog, mock_ctx, download_repository):
    await system_cog.list_files.callback(system_cog, mock_ctx)
    mock_ctx.send.assert_called_once_with("No tracked downloaded files.")

@pytest.mark.asyncio
async def test_list_files_not_empty(system_cog, mock_ctx, download_repository):
    # Insert data
    download_repository.add_downloaded_file("http://url1", "/path/to/[3D] very_long_filename_that_should_be_truncated_at_some_point.mp4")
    # ID is 1
    download_repository.update_downloaded_file_status(1, 0) # Set to private
    
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
async def test_delete_file_success(system_cog, mock_ctx, download_repository):
    # Insert data
    download_repository.add_downloaded_file("url1", "/path/to/file1.mp4")
    
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1")
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        assert download_repository.get_downloaded_file_by_id(1) is None
        mock_ctx.send.assert_called_once_with("ID 1: Deleted from disk and DB.")

@pytest.mark.asyncio
async def test_delete_file_multiple(system_cog, mock_ctx, download_repository):
    # Insert data for ID 1 and 2
    download_repository.add_downloaded_file("url1", "/path/to/file1.mp4") # ID 1
    download_repository.add_downloaded_file("url2", "/path/to/file2.mp4") # ID 2
    
    with patch("os.path.exists", side_effect=[True, False]), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1 3 2")
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        assert download_repository.get_downloaded_file_by_id(1) is None
        assert download_repository.get_downloaded_file_by_id(2) is None
        
        expected_output = "ID 1: Deleted from disk and DB.\nID 3: No file found.\nID 2: Not on disk, record removed from DB."
        mock_ctx.send.assert_called_once_with(expected_output)

@pytest.mark.asyncio
async def test_delete_file_not_found_on_disk(system_cog, mock_ctx, download_repository):
    download_repository.add_downloaded_file("url1", "/path/to/file1.mp4")
    
    with patch("os.path.exists", return_value=False):
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1")
        
        assert download_repository.get_downloaded_file_by_id(1) is None
        mock_ctx.send.assert_called_once_with("ID 1: Not on disk, record removed from DB.")

@pytest.mark.asyncio
async def test_delete_file_not_in_db(system_cog, mock_ctx, download_repository):
    await system_cog.delete_file.callback(system_cog, mock_ctx, "1")
    mock_ctx.send.assert_called_once_with("ID 1: No file found.")

@pytest.mark.asyncio
async def test_delete_file_multiple_comma_separated(system_cog, mock_ctx, download_repository):
    download_repository.add_downloaded_file("url1", "/path/to/file1.mp4") # 1
    download_repository.add_downloaded_file("url2", "/path/to/file2.mp4") # 2
    
    with patch("os.path.exists", side_effect=[True, False]), \
         patch("os.remove") as mock_remove:
        await system_cog.delete_file.callback(system_cog, mock_ctx, "1, 3,2")
        
        mock_remove.assert_called_once_with("/path/to/file1.mp4")
        
        expected_output = "ID 1: Deleted from disk and DB.\nID 3: No file found.\nID 2: Not on disk, record removed from DB."
        mock_ctx.send.assert_called_once_with(expected_output)

@pytest.mark.asyncio
async def test_delete_file_invalid_input(system_cog, mock_ctx, download_repository):
    await system_cog.delete_file.callback(system_cog, mock_ctx, "1 abc 3")
    mock_ctx.send.assert_called_once_with("Please provide a valid list of integer IDs separated by spaces or commas.")

@pytest.mark.asyncio
async def test_delete_file_empty_input(system_cog, mock_ctx, download_repository):
    await system_cog.delete_file.callback(system_cog, mock_ctx, "  ")
    mock_ctx.send.assert_called_once_with("Please provide at least one file ID.")

@pytest.mark.asyncio
async def test_purge_files(system_cog, mock_ctx, download_repository):
    download_repository.add_downloaded_file("url1", "/path/exists")
    download_repository.add_downloaded_file("url2", "/path/missing")
    
    def exists_side_effect(path):
        return path == "/path/exists"

    with patch("os.path.exists", side_effect=exists_side_effect):
        await system_cog.purge_files.callback(system_cog, mock_ctx)
        
        assert download_repository.get_downloaded_file_by_id(1) is not None
        assert download_repository.get_downloaded_file_by_id(2) is None
        mock_ctx.send.assert_called_once_with("Purged 1 records from the database for missing files.")

@pytest.mark.asyncio
async def test_scan_files_no_arg(system_cog, mock_ctx, download_repository, mock_downloader):
    # Setup test data:
    # 1. New file (is_public is NULL) - should be scanned
    download_repository.add_downloaded_file("url_new", "/path1") 
    # 2. Public file (is_public is 1) - should NOT be scanned
    download_repository.add_downloaded_file("url_pub", "/path2")
    download_repository.update_downloaded_file_status(2, 1)
    # 3. Private file (is_public is 0) - should NOT be scanned
    download_repository.add_downloaded_file("url_priv", "/path3")
    download_repository.update_downloaded_file_status(3, 0)
    
    mock_downloader.check_video_availability.return_value = True
    
    await system_cog.scan_files.callback(system_cog, mock_ctx)
    
    # Should only scan the NULL one
    mock_downloader.check_video_availability.assert_called_once_with("url_new")
    
    # Verify summary message
    sent_msgs = [call.args[0] for call in mock_ctx.send.call_args_list]
    assert any("Scan complete. Scanned: 1, Still Public: 1, Now Private/Unavailable: 0" in m for m in sent_msgs)

@pytest.mark.asyncio
async def test_scan_files_with_older_than(system_cog, mock_ctx, download_repository, mock_downloader):
    # Setup test data:
    # 1. New file (is_public is NULL) - should be scanned
    download_repository.add_downloaded_file("url_new", "/path1") # ID 1
    # 2. Recently checked public file (last_check is now) - should NOT be scanned
    download_repository.add_downloaded_file("url_pub_recent", "/path2") # ID 2
    download_repository.update_downloaded_file_status(2, 1)
    # 3. Old public file (last_check is 1 week ago) - SHOULD be scanned
    download_repository.add_downloaded_file("url_pub_old", "/path3") # ID 3
    with download_repository.con:
        download_repository.con.execute("UPDATE downloaded_files SET is_public = 1, last_check = unixepoch() - (86400 * 7) WHERE id = 3")
    
    mock_downloader.check_video_availability.side_effect = [True, False]
    
    # Scan files older than 3 days
    await system_cog.scan_files.callback(system_cog, mock_ctx, older_than="3d")
    
    # Should scan ID 1 and ID 3
    assert mock_downloader.check_video_availability.call_count == 2
    mock_downloader.check_video_availability.assert_any_call("url_new")
    mock_downloader.check_video_availability.assert_any_call("url_pub_old")
    
    # Verify result for ID 3 was updated to 0 (since check_video_availability returned False for the 2nd call)
    files = download_repository.get_downloaded_files()
    id_3_info = next(f for f in files if f[0] == 3)
    assert id_3_info[4] == 0 # is_public is 0 (Now Private/Unavailable)
    
    # Verify summary message
    sent_msgs = [call.args[0] for call in mock_ctx.send.call_args_list]
    assert any("Scan complete. Scanned: 2, Still Public: 1, Now Private/Unavailable: 1" in m for m in sent_msgs)
