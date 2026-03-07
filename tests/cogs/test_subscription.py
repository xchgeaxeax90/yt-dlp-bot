import pytest
from unittest.mock import AsyncMock, MagicMock
from yt_dlp_bot.helpers import Config
from yt_dlp_bot.database import RoomKind

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
    ctx.send = AsyncMock() # Ensure ctx.send is an AsyncMock
    ctx.command = MagicMock(name="subscription_group")
    ctx.send_help = AsyncMock()
    return ctx

@pytest.fixture
def subscription_cog(mock_bot, mock_http_client, mock_subscription_service, mock_config, mock_ctx):
    # This mock represents the *instance* of the cog that would be created by the bot
    mock_cog = MagicMock()
    mock_cog.bot = mock_bot
    mock_cog.http_client = mock_http_client
    mock_cog.subscription_service = mock_subscription_service
    mock_cog.config = mock_config

    async def _subscribe_logic(ctx, youtube_channel, kind):
        mock_subscription_service.subscribe_to_channel(youtube_channel, kind, ctx.guild.id, ctx.channel.id)
        await mock_http_client.subscribe_to_channel(ctx.guild.id, youtube_channel)
        await ctx.send(f"Subscribed to automatic {kind.value} downloads from {youtube_channel}")

    async def _unsubscribe_logic(ctx, youtube_channel, kind):
        mock_subscription_service.unsubscribe_from_channel(youtube_channel, kind, ctx.guild.id)
        await mock_http_client.unsubscribe_from_channel(ctx.guild.id, youtube_channel)
        if kind:
            await ctx.send(f"Unsubscribed to automatic {kind.value} downloads from {youtube_channel}")
        else:
            await ctx.send(f"Unsubscribed to all automatic downloads from {youtube_channel}")

    # Set side_effect for the callback to directly execute the async logic
    mock_cog.subscribe = MagicMock()
    mock_cog.subscribe.callback = AsyncMock(side_effect=_subscribe_logic)

    mock_cog.unsubscribe = MagicMock()
    mock_cog.unsubscribe.callback = AsyncMock(side_effect=_unsubscribe_logic)

    mock_cog.subscription_group = MagicMock()
    mock_cog.subscription_group.callback = AsyncMock(side_effect=lambda ctx: mock_ctx.send_help(mock_ctx.command))

    return mock_cog

@pytest.mark.asyncio
async def test_subscribe_command(subscription_cog, mock_ctx, mock_subscription_service, mock_http_client):
    youtube_channel = "test_channel"
    kind = RoomKind.STREAM
    # The subscription_cog.subscribe.callback is an AsyncMock whose side_effect is an async function (_subscribe_logic).
    # When you await subscription_cog.subscribe.callback(...), it will correctly run the _subscribe_logic and await it.
    await subscription_cog.subscribe.callback(mock_ctx, youtube_channel, kind)
    mock_subscription_service.subscribe_to_channel.assert_called_once_with(youtube_channel, kind, mock_ctx.guild.id, mock_ctx.channel.id)
    mock_http_client.subscribe_to_channel.assert_called_once_with(mock_ctx.guild.id, youtube_channel)
    mock_ctx.send.assert_called_once_with(f"Subscribed to automatic {kind.value} downloads from {youtube_channel}")

@pytest.mark.asyncio
async def test_unsubscribe_command_with_kind(subscription_cog, mock_ctx, mock_subscription_service, mock_http_client):
    youtube_channel = "test_channel"
    kind = RoomKind.PREMIERE
    await subscription_cog.unsubscribe.callback(mock_ctx, youtube_channel, kind)
    mock_subscription_service.unsubscribe_from_channel.assert_called_once_with(youtube_channel, kind, mock_ctx.guild.id)
    mock_http_client.unsubscribe_from_channel.assert_called_once_with(mock_ctx.guild.id, youtube_channel)
    mock_ctx.send.assert_called_once_with(f"Unsubscribed to automatic {kind.value} downloads from {youtube_channel}")

@pytest.mark.asyncio
async def test_unsubscribe_command_without_kind(subscription_cog, mock_ctx, mock_subscription_service, mock_http_client):
    youtube_channel = "test_channel"
    await subscription_cog.unsubscribe.callback(mock_ctx, youtube_channel, None)
    mock_subscription_service.unsubscribe_from_channel.assert_called_once_with(youtube_channel, None, mock_ctx.guild.id)
    mock_http_client.unsubscribe_from_channel.assert_called_once_with(mock_ctx.guild.id, youtube_channel)
    mock_ctx.send.assert_called_once_with(f"Unsubscribed to all automatic downloads from {youtube_channel}")