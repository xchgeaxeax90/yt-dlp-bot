import pytest
from unittest.mock import AsyncMock, MagicMock
from yt_dlp_bot.cogs.ytdl import YtDl
from yt_dlp_bot.helpers import Config

@pytest.fixture
def mock_bot():
    return AsyncMock()

@pytest.fixture
def mock_http_client():
    return AsyncMock()

@pytest.fixture
def mock_download_repository():
    return MagicMock()

@pytest.fixture
def mock_download_service():
    mock_service = MagicMock()
    mock_service.initiate_download = AsyncMock() # This one is awaited in the cog
    return mock_service

@pytest.fixture
def mock_scheduler_service():
    return MagicMock()

@pytest.fixture
def mock_config():
    # Provide a default mock config. Can be updated in tests as needed.
    config = Config()
    config.yt_dlp_config = {'paths': {'home': '/test/download/path'}}
    return config

@pytest.fixture
def ytdl_cog(mock_bot, mock_http_client, mock_download_repository, mock_download_service, mock_scheduler_service, mock_config):
    return YtDl(
        mock_bot,
        mock_http_client,
        mock_download_repository,
        mock_download_service,
        mock_scheduler_service,
        mock_config
    )

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.channel.id = 123
    ctx.guild.id = 456
    return ctx

@pytest.mark.asyncio
async def test_on_ready(ytdl_cog, mock_scheduler_service):
    await ytdl_cog.on_ready()
    mock_scheduler_service.start.assert_called_once()

@pytest.mark.asyncio
async def test_download_command(ytdl_cog, mock_ctx, mock_download_service):
    url = "https://example.com/video"
    mock_download_service.initiate_download.return_value = "Download initiated."
    await ytdl_cog.download.callback(ytdl_cog, mock_ctx, url)
    mock_ctx.defer.assert_called_once()
    mock_download_service.initiate_download.assert_called_once_with(url, mock_ctx.guild.id, mock_ctx.channel.id)
    mock_ctx.send.assert_called_once_with("Download initiated.")

@pytest.mark.asyncio
async def test_scheduled_download_command(ytdl_cog, mock_ctx, mock_download_service):
    url = "https://example.com/video"
    timestamp = "2024-03-07 10:00:00"
    mock_download_service.schedule_download.return_value = "Scheduled download."
    await ytdl_cog.scheduled_download.callback(ytdl_cog, mock_ctx, url, timestamp)
    mock_download_service.schedule_download.assert_called_once_with(url, timestamp, mock_ctx.guild.id, mock_ctx.channel.id)
    mock_ctx.send.assert_called_once_with("Scheduled download.")

@pytest.mark.asyncio
async def test_streamlink_download_command(ytdl_cog, mock_ctx, mock_download_service):
    url = "https://example.com/stream"
    mock_download_service.initiate_download.return_value = "Streamlink download initiated."
    await ytdl_cog.streamlink_download.callback(ytdl_cog, mock_ctx, url)
    mock_download_service.initiate_download.assert_called_once_with(url, mock_ctx.guild.id, mock_ctx.channel.id, streamlink=True)
    mock_ctx.send.assert_called_once_with(f"Streamlink download initiated. <{url}>")

@pytest.mark.asyncio
async def test_running_downloads_command(ytdl_cog, mock_ctx, mock_download_service):
    mock_download_service.get_running_downloads.return_value = "Running downloads list"
    await ytdl_cog.running_downloads.callback(ytdl_cog, mock_ctx)
    mock_download_service.get_running_downloads.assert_called_once()
    mock_ctx.send.assert_called_once_with("Running downloads list")

@pytest.mark.asyncio
async def test_scheduled_downloads_command(ytdl_cog, mock_ctx, mock_download_service):
    mock_download_service.get_scheduled_downloads.return_value = "Scheduled downloads list"
    await ytdl_cog.scheduled_downloads.callback(ytdl_cog, mock_ctx)
    mock_download_service.get_scheduled_downloads.assert_called_once()
    mock_ctx.send.assert_called_once_with("Scheduled downloads list")

@pytest.mark.asyncio
async def test_cancel_download_command(ytdl_cog, mock_ctx, mock_download_service):
    url = "https://example.com/video"
    mock_download_service.cancel_download.return_value = "Download cancelled"
    await ytdl_cog.cancel_download.callback(ytdl_cog, mock_ctx, url)
    mock_download_service.cancel_download.assert_called_once_with(url)
    mock_ctx.send.assert_called_once_with("Download cancelled")

