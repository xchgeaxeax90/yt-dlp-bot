import pytest
from unittest.mock import MagicMock, AsyncMock
from yt_dlp_bot.services.subscription_service import SubscriptionService
from yt_dlp_bot.database import YoutubeWaitingRoom, YoutubeVideo, RoomKind

@pytest.fixture
def mock_sub_repo():
    return MagicMock()

@pytest.fixture
def mock_down_repo():
    return MagicMock()

@pytest.fixture
def mock_down_service():
    return AsyncMock()

@pytest.fixture
def mock_http_client():
    return MagicMock()

@pytest.fixture
def subscription_service(mock_sub_repo, mock_http_client, mock_down_service, mock_down_repo):
    return SubscriptionService(mock_sub_repo, mock_http_client, mock_down_service, mock_down_repo)

def test_subscribe_to_channel(subscription_service, mock_sub_repo):
    subscription_service.subscribe_to_channel("chan1", RoomKind.STREAM, 1, 2)
    mock_sub_repo.subscribe_to_channel.assert_called_once_with("chan1", RoomKind.STREAM, 1, 2)

def test_unsubscribe_from_channel(subscription_service, mock_sub_repo):
    subscription_service.unsubscribe_from_channel("chan1", RoomKind.STREAM, 1)
    mock_sub_repo.unsubscribe_from_channel.assert_called_once_with("chan1", RoomKind.STREAM, 1)

def test_receive_waiting_room_when_subscribed(subscription_service, mock_down_repo, mock_sub_repo):
    room = YoutubeWaitingRoom(channel_id="chan1", video_id="vid1", title="test", kind=RoomKind.STREAM, utcepoch=1234)
    # Mocking download_repository.add_subscribed_waiting_room to return True
    mock_down_repo.add_subscribed_waiting_room.return_value = True
    # Mocking subscription_repository.get_guild_info_for_subscription to return guild/channel info
    mock_sub_repo.get_guild_info_for_subscription.return_value = [(10, 20)]
    
    subscription_service.receive_waiting_room(room)
    
    mock_down_repo.add_subscribed_waiting_room.assert_called_once()
    mock_sub_repo.get_guild_info_for_subscription.assert_called_once_with("chan1", RoomKind.STREAM)
    mock_down_repo.add_completion_for_url.assert_called_once_with(10, 20, room.url)

def test_receive_waiting_room_when_not_subscribed(subscription_service, mock_down_repo, mock_sub_repo):
    room = YoutubeWaitingRoom(channel_id="chan1", video_id="vid1", title="test", kind=RoomKind.STREAM, utcepoch=1234)
    mock_down_repo.add_subscribed_waiting_room.return_value = False
    
    subscription_service.receive_waiting_room(room)
    
    mock_down_repo.add_subscribed_waiting_room.assert_called_once()
    mock_sub_repo.get_guild_info_for_subscription.assert_not_called()

@pytest.mark.asyncio
async def test_receive_stream_notification_when_subscribed(subscription_service, mock_sub_repo, mock_down_repo, mock_down_service):
    video = YoutubeVideo(channel_id="chan1", video_id="vid1")
    mock_sub_repo.get_guild_info_for_subscription.return_value = [(10, 20)]
    
    await subscription_service.receive_stream_notification(video)
    
    mock_sub_repo.get_guild_info_for_subscription.assert_called_once_with("chan1", RoomKind.STREAM)
    mock_down_repo.add_completion_for_url.assert_called_once_with(10, 20, video.url)
    mock_down_service.initiate_download.assert_called_once_with(video.url, 10, 20, streamlink=True)

@pytest.mark.asyncio
async def test_receive_stream_notification_when_not_subscribed(subscription_service, mock_sub_repo, mock_down_repo, mock_down_service):
    video = YoutubeVideo(channel_id="chan1", video_id="vid1")
    mock_sub_repo.get_guild_info_for_subscription.return_value = []
    
    await subscription_service.receive_stream_notification(video)
    
    mock_sub_repo.get_guild_info_for_subscription.assert_called_once()
    mock_down_repo.add_completion_for_url.assert_not_called()
    mock_down_service.initiate_download.assert_not_called()

def test_get_subscriptions(subscription_service, mock_sub_repo):
    # Mock data from subscription_repository.get_subscriptions
    mock_sub_repo.get_subscriptions.return_value = [
        (123, 456, "chan1", "streams"),
        (123, 789, "chan2", "videos")
    ]
    
    subscriptions = subscription_service.get_subscriptions(123)
    
    mock_sub_repo.get_subscriptions.assert_called_once_with(123)
    assert len(subscriptions) == 2
    assert subscriptions[0].guild_id == 123
    assert subscriptions[0].channel_id == 456
    assert subscriptions[0].youtube_channel == "chan1"
    assert subscriptions[0].kind == RoomKind.STREAM
    assert subscriptions[1].guild_id == 123
    assert subscriptions[1].channel_id == 789
    assert subscriptions[1].youtube_channel == "chan2"
    assert subscriptions[1].kind == RoomKind.PREMIERE
