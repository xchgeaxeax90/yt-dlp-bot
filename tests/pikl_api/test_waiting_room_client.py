import pytest
import json
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from yt_dlp_bot.pikl_api.waiting_room_client import AsyncSSEClient
from yt_dlp_bot.pikl_api.http_client import AsyncHttpClient
from yt_dlp_bot.database import YoutubeVideo

@pytest.fixture
def mock_sub_service():
    return AsyncMock()

@pytest.fixture
def client(mock_sub_service):
    return AsyncSSEClient("http://pikl", mock_sub_service)

@pytest.mark.asyncio
async def test_handle_event(client, mock_sub_service):
    data = {'channel_id': 'chan1', 'video_id': 'vid1'}
    await client.handle_event(data)
    
    # Check if receive_stream_notification was called with correct YoutubeVideo
    mock_sub_service.receive_stream_notification.assert_called_once()
    video = mock_sub_service.receive_stream_notification.call_args[0][0]
    assert isinstance(video, YoutubeVideo)
    assert video.channel_id == 'chan1'
    assert video.video_id == 'vid1'

@pytest.mark.asyncio
async def test_async_http_client_subscribe(mock_sub_service):
    with patch('httpx.AsyncClient.put', new_callable=AsyncMock) as mock_put:
        client = AsyncHttpClient("http://pikl")
        await client.subscribe_to_channel(123, "chan1")
        
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        assert args[0] == "http://pikl/subscriptions"
        assert kwargs['params'] == {'guild_id': 123, 'youtube_channel': 'chan1'}

@pytest.mark.asyncio
async def test_async_http_client_unsubscribe(mock_sub_service):
    with patch('httpx.AsyncClient.delete', new_callable=AsyncMock) as mock_delete:
        client = AsyncHttpClient("http://pikl")
        await client.unsubscribe_from_channel(123, "chan1")
        
        mock_delete.assert_called_once()
        args, kwargs = mock_delete.call_args
        assert args[0] == "http://pikl/subscriptions"
        assert kwargs['params'] == {'guild_id': 123, 'youtube_channel': 'chan1'}
