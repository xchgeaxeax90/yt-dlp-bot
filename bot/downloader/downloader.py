import yt_dlp
import logging
import asyncio
from dataclasses import dataclass
from concurrent import futures

from bot.database import db
from bot.helpers import config, fetch_guild, fetch_channel
import datetime

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

def hook(d):
    logger.info(d)

class Downloader:
    def __init__(self, bot):
        self.executor = futures.ThreadPoolExecutor(max_workers=None)
        self.bot = bot

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
                timestamp = int(video_info['release_timestamp'])
                time = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                return AvailableFuture(time)
            else:
                return AvailableNow
        except Exception as e:
            return AvailabilityError(str(e))

    async def _post_completion(self, url: str):
        logger.info("Post completion")
        completion = db.get_completion_channel_for_url(url)
        if completion:
            (guild_id, channel_id) = completion
            guild = await fetch_guild(self.bot, guild_id)
            channel = await fetch_channel(guild, channel_id)
            await channel.send(f"Finished downloading {url}")


    def _download(self, url: str, extra_args: dict):
        logger.info("Attempting to submit post completion")
        with yt_dlp.YoutubeDL(config.yt_dlp_config | extra_args) as ydl:
            logger.info(f'Initiating download of {url}')
            ydl.download(url)
            logger.info(f'Finished download of {url}')

    async def download_async(self, url: str, guild_id=None, channel_id=None):
        #self._download(url)
        if guild_id and channel_id:
            db.add_completion_for_url(guild_id, channel_id, url)
        await asyncio.to_thread(self._download, url, {})
        await self._post_completion(url)

    def defer_download_until_time(self, url: str, time: datetime, guild_id=None, channel_id=None):
        utctimestamp = time.timestamp()
        logger.info(f'Deferring download of {url} until {utctimestamp}')
        db.add_future_download(url, utctimestamp)
        if guild_id and channel_id:
            db.add_completion_for_url(guild_id, channel_id, url)
    

    async def schedule_deferred_downloads(self):
        urls = db.get_downloads_now(60*2)
        [db.delete_future_download(url) for url in urls]
        logger.info(f'Downloading {urls}')
        async def _run_download(url):
            await asyncio.to_thread(self._download, url, {'wait_for_video': (15, 2*60*60)})
            await self._post_completion(url)

        tasks = [_run_download(url) for url in urls]
        await asyncio.gather(*tasks)
        
        
