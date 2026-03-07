import logging
from typing import Optional

from yt_dlp_bot.repositories.subscription_repository import SubscriptionRepository
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.pikl_api.http_client import AsyncHttpClient
from yt_dlp_bot.services.download_service import DownloadService
from yt_dlp_bot.database import YoutubeWaitingRoom, YoutubeVideo, RoomKind, SubscriptionModel, SubscriptionModel

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, subscription_repository: SubscriptionRepository, http_client: AsyncHttpClient, download_service: DownloadService, download_repository: DownloadRepository):
        self.subscription_repository = subscription_repository
        self.http_client = http_client
        self.download_service = download_service
        self.download_repository = download_repository

    def subscribe_to_channel(self, youtube_channel: str, kind: RoomKind, guild_id: int, channel_id: int):
        self.subscription_repository.subscribe_to_channel(youtube_channel, kind, guild_id, channel_id)
        # Assuming http_client.subscribe_to_channel is synchronous or we don't need to await it
        # For now, it's called here, but if it's async, it should be awaited.
        # Check AsyncHttpClient in yt_dlp_bot/pikl_api/waiting_room_client.py
        # It's AsyncHttpClient, so it should be awaited.
        # This will be fixed when integrating into ytdl cog as async function.
        # For now, keeping it as is here.
        # Awaiting it directly here would block the event loop if not careful.
        # The service method itself might need to be async if it awaits this.
        # Let's make it async.
        # No, the cog will call this method. The cog handles the await.
        pass # The actual API call will be done in the cog

    def unsubscribe_from_channel(self, youtube_channel: str, kind: RoomKind | None, guild_id: int):
        self.subscription_repository.unsubscribe_from_channel(youtube_channel, kind, guild_id)
        # Similar to subscribe, http_client call will be in cog
        pass

    def receive_waiting_room(self, room: YoutubeWaitingRoom):
        # Logic from Downloader.receive_waiting_room
        if self.download_repository.add_subscribed_waiting_room(room, room.url):
            guild_info = self.subscription_repository.get_guild_info_for_subscription(room.channel_id, room.kind)
            for (guild_id, channel_id) in guild_info:
                logger.info(f"Adding completion for {room.url}")
                self.download_repository.add_completion_for_url(guild_id, channel_id, room.url)

    async def receive_stream_notification(self, video: YoutubeVideo):
        # Logic from Downloader.receive_stream_notification
        guild_info = self.subscription_repository.get_guild_info_for_subscription(video.channel_id, RoomKind.STREAM)
        if guild_info:
            # We take the first guild/channel as a "primary" for the initiate_download call
            # But we record completion for all of them
            for (guild_id, channel_id) in guild_info:
                logger.info(f"Adding completion for {video.url}")
                self.download_repository.add_completion_for_url(guild_id, channel_id, video.url)
            
            # Use the first one to start the download through service
            first_guild, first_channel = guild_info[0]
            await self.download_service.initiate_download(video.url, first_guild, first_channel, streamlink=True)

    def get_subscriptions(self, guild_id: int) -> list[SubscriptionModel]:
        raw_subscriptions = self.subscription_repository.get_subscriptions(guild_id)
        subscriptions = []
        for guild_id, channel_id, youtube_channel, room_kind_value in raw_subscriptions:
            subscriptions.append(SubscriptionModel(
                guild_id=guild_id,
                channel_id=channel_id,
                youtube_channel=youtube_channel,
                kind=RoomKind(room_kind_value)
            ))
        return subscriptions
