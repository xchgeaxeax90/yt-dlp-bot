import pytest
from unittest.mock import AsyncMock, MagicMock
from yt_dlp_bot.helpers import Config
from yt_dlp_bot.database import RoomKind
from yt_dlp_bot.cogs.subscription import Subscription

# No import of the actual Subscription cog here to avoid decorator side effects.

@pytest.fixture
def mock_bot():
    bot_mock = AsyncMock()
    return bot_mock

@pytest.fixture
def mock_http_client():
    return AsyncMock()

@pytest.fixture
def mock_subscription_service():
    return MagicMock()

@pytest.fixture
def mock_config():
    config = Config()
    config.yt_dlp_config = {'paths': {'home': '/test/download/path'}}
    return config

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.channel.id = 123
    ctx.guild.id = 456
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture
def subscription_cog(mock_bot, mock_http_client, mock_subscription_service, mock_config):
    return Subscription(mock_bot, mock_http_client, mock_subscription_service, mock_config)

@pytest.mark.asyncio
async def test_subscribe_command(subscription_cog, mock_ctx, mock_subscription_service, mock_http_client):
    youtube_channel = "test_channel"
    kind = RoomKind.STREAM
    await subscription_cog.subscribe.callback(subscription_cog, mock_ctx, youtube_channel, kind)
    mock_subscription_service.subscribe_to_channel.assert_called_once_with(youtube_channel, kind, mock_ctx.guild.id, mock_ctx.channel.id)
    mock_http_client.subscribe_to_channel.assert_called_once_with(mock_ctx.guild.id, youtube_channel)
    mock_ctx.send.assert_called_once_with(f"Subscribed to automatic {kind.value} downloads from {youtube_channel}")

@pytest.mark.asyncio
async def test_unsubscribe_command_with_kind(subscription_cog, mock_ctx, mock_subscription_service, mock_http_client):
    youtube_channel = "test_channel"
    kind = RoomKind.PREMIERE
    await subscription_cog.unsubscribe.callback(subscription_cog, mock_ctx, youtube_channel, kind)
    mock_subscription_service.unsubscribe_from_channel.assert_called_once_with(youtube_channel, kind, mock_ctx.guild.id)
    mock_http_client.unsubscribe_from_channel.assert_called_once_with(mock_ctx.guild.id, youtube_channel)
    mock_ctx.send.assert_called_once_with(f"Unsubscribed to automatic {kind.value} downloads from {youtube_channel}")

@pytest.mark.asyncio
async def test_unsubscribe_command_without_kind(subscription_cog, mock_ctx, mock_subscription_service, mock_http_client):
    youtube_channel = "test_channel"
    await subscription_cog.unsubscribe.callback(subscription_cog, mock_ctx, youtube_channel, None)
    mock_subscription_service.unsubscribe_from_channel.assert_called_once_with(youtube_channel, None, mock_ctx.guild.id)
    mock_http_client.unsubscribe_from_channel.assert_called_once_with(mock_ctx.guild.id, youtube_channel)
    mock_ctx.send.assert_called_once_with(f"Unsubscribed to all automatic downloads from {youtube_channel}")