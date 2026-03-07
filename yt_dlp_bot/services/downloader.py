import yt_dlp
import logging
import asyncio
from dataclasses import dataclass
from concurrent import futures

from yt_dlp_bot.database import YoutubeWaitingRoom, YoutubeVideo, RoomKind
from yt_dlp_bot.helpers import config
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.repositories.subscription_repository import SubscriptionRepository
from yt_dlp_bot.services.notification_service import NotificationService
import datetime
import threading
import os

logger = logging.getLogger(__name__)

# Algebraic data type for video availability
@dataclass
class AvailableFuture:
    epoch: datetime.datetime

@dataclass
class AvailableNow:
    pass

@dataclass
class AvailabilityError:
    errorstr: str

Availability = AvailableFuture | AvailableNow | AvailabilityError

class Downloader:
    def __init__(self, download_repository: DownloadRepository, subscription_repository: SubscriptionRepository, notification_service: NotificationService):
        self.executor = futures.ThreadPoolExecutor(max_workers=None)
        self.download_repository = download_repository
        self.subscription_repository = subscription_repository
        self.notification_service = notification_service

    def get_info(self, url: str):
        extra_opts = {'ignore_no_formats_error': True}
        with yt_dlp.YoutubeDL(config.yt_dlp_config | extra_opts) as ydl:
            info = ydl.extract_info(url, download=False, process=False)
            return info

    async def get_availability(self, url: str) -> Availability:
        try:
            video_info = await asyncio.to_thread(self.get_info, url)
            if not 'live_status' in video_info:
                return AvailabilityError('No live status found in video info')
            if video_info['live_status'] == 'is_upcoming':
                # This video is not live yet and must have a download scheduled
                if not 'release_timestamp' in video_info:
                    return AvailabilityError('No timestamp found in video info, cannot schedule a download')
                logger.info(f'Received timestamp {video_info["release_timestamp"]}')
                if 'release_timestamp' in video_info and video_info['release_timestamp']:
                    timestamp = int(video_info['release_timestamp'])
                    time = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                    return AvailableFuture(time)
                else:
                    return AvailableFuture(datetime.datetime.now())
            else:
                return AvailableNow()
        except Exception as e:
            return AvailabilityError(str(e))

    def defer_download_until_time(self, url: str, time: datetime, guild_id=None, channel_id=None):
        utctimestamp = time.timestamp()
        logger.info(f'Deferring download of {url} until {utctimestamp}')
        self.download_repository.add_future_download(url, int(utctimestamp))
        if guild_id and channel_id:
            self.download_repository.add_completion_for_url(guild_id, channel_id, url)

    def get_scheduled_downloads(self):
        return self.download_repository.get_all_scheduled_downloads()

    def cancel_scheduled_download(self, url):
        scheduled_downloads = self.download_repository.get_all_scheduled_downloads()
        urls = {r[0] for r in scheduled_downloads}
        if url in urls:
            # Disable here because we want it to reject nuisance updates from the pikl api if we delete a waiting room
            self.download_repository.disable_future_download(url)
            return True
        return False
