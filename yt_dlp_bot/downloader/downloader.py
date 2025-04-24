import yt_dlp
import logging
import asyncio
from dataclasses import dataclass
from concurrent import futures

from yt_dlp_bot.database import db
from yt_dlp_bot.helpers import config, fetch_guild, fetch_channel
import datetime
import threading

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

@dataclass
class DownloadTask:
    task: asyncio.Task
    event: threading.Event
    

class Downloader:
    def __init__(self, bot):
        self.executor = futures.ThreadPoolExecutor(max_workers=None)
        self.bot = bot
        self.current_downloads = {}

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


    async def _download(self, url: str, extra_args: dict, event: threading.Event):
        def _download_hook(event, d):
            logger.info(f'Checking event {event}')
            if event.is_set():
                print('Attempting to cancel yt-dlp')
                raise asyncio.CancelledError
        hook_args = {'progress_hooks': [lambda d: _download_hook(event, d)]}
        def _download_impl():
            with yt_dlp.YoutubeDL(config.yt_dlp_config | extra_args | hook_args) as ydl:
                logger.info(f'Initiating download of {url}')
                ydl.download(url)
                logger.info(f'Finished download of {url}')
        await asyncio.to_thread(_download_impl)
        await self._post_completion(url)

    def create_download_task(self, url: str, extra_args: dict):
        event = threading.Event()
        task = asyncio.create_task(self._download(url, extra_args, event))
        return DownloadTask(task, event)

    async def download_async(self, url: str, guild_id=None, channel_id=None):
        #self._download(url)
        if guild_id and channel_id:
            db.add_completion_for_url(guild_id, channel_id, url)
        task = self.create_download_task(url, {})
        self.current_downloads[url] = task
        await asyncio.wait([v.task for v in self.current_downloads.values()], timeout=1)

    def defer_download_until_time(self, url: str, time: datetime, guild_id=None, channel_id=None):
        utctimestamp = time.timestamp()
        logger.info(f'Deferring download of {url} until {utctimestamp}')
        db.add_future_download(url, utctimestamp)
        if guild_id and channel_id:
            db.add_completion_for_url(guild_id, channel_id, url)
    

    async def schedule_deferred_downloads(self, loop_interval_s):
        urls = db.get_downloads_now(60*2)
        [db.delete_future_download(url) for url in urls]
        if urls:
            logger.info(f'Downloading {urls}')
        extra_args = {'wait_for_video': [15, 60]}

        # Start asyncio tasks for each video to be downloaded
        tasks = {url: self.create_download_task(url, extra_args) for url in urls }
        # The tricky bit, we cannot asyncio.gather(*tasks) here, as it
        # would block the loop calling this task until every scheduled
        # download finishes

        # Instead, we will store all the currently executing tasks in the object
        self.current_downloads.update(tasks)
        if not self.current_downloads:
            return

        logger.info(f'Waiting for {self.current_downloads.values()} to finish')
        # Use asyncio.wait to wait with a timeout of the loop polling interval
        # If the tasks finish before the timeout, great, this is equivalent to asyncio.gather
        # If not however, the tasks being waited on will not be
        # cancelled, and can be awaited on again in the next loop
        await asyncio.wait([v.task for v in self.current_downloads.values()], timeout=loop_interval_s)

        urls_to_delete = []
        for url, task in self.current_downloads.items():
            if task.task.done():
                urls_to_delete.append(url)
            logger.info(f'Finished download for {url}')
        [self.current_downloads.pop(url) for url in urls_to_delete]
        
    def get_running_downloads(self):
        return self.current_downloads.keys()

    def get_scheduled_downloads(self):
        return db.get_all_scheduled_downloads()

    def cancel_download(self, url):
        if url in self.current_downloads:
            logger.info(f'Setting event {self.current_downloads[url].event}')
            self.current_downloads[url].event.set()
            return True
        scheduled_downloads = db.get_all_scheduled_downloads()
        urls = {r[0] for r in scheduled_downloads}
        if url in urls:
            # Disable here because we want it to reject nuisance updates from the pikl api if we delete a waiting room
            db.disable_future_download(url)
            return True
        return False
        
