import logging
import asyncio
import datetime
import threading
import os
from dataclasses import dataclass

import yt_dlp

from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.services.notification_service import NotificationService
from yt_dlp_bot.helpers import config
from yt_dlp_bot.services.downloader import Downloader


logger = logging.getLogger(__name__)

@dataclass
class DownloadTask:
    task: asyncio.Task
    event: threading.Event

class DownloadManager:
    def __init__(self, downloader: Downloader, download_repository: DownloadRepository, notification_service: NotificationService):
        self.downloader = downloader
        self.download_repository = download_repository
        self.notification_service = notification_service
        self.current_downloads = {} # Stores DownloadTask objects

    async def _notify_for_download(self, url: str, message: str):
        logger.info("Post completion")
        completion = self.download_repository.get_completion_channel_for_url(url)
        if completion:
            (guild_id, channel_id) = completion
            await self.notification_service.notify(guild_id, channel_id, message)

    async def _download(self, url: str, notify: bool, extra_args: dict, event: threading.Event):
        if notify:
            await self._notify_for_download(url, f'Started download of <{url}>')
        def _download_hook(event, d):
            logger.info(f'Checking event {event}')
            if event.is_set():
                print('Attempting to cancel yt-dlp')
                raise asyncio.CancelledError
        hook_args = {'progress_hooks': [lambda d: _download_hook(event, d)]}
        def _download_impl():
            with yt_dlp.YoutubeDL(config.yt_dlp_config | extra_args | hook_args) as ydl:
                logger.info(f'Initiating download of {url}')
                info = ydl.extract_info(url, download=True)
                if not info:
                    logger.error(f'Failed to extract info for {url}')
                    return None
                filename = ydl.prepare_filename(info)
                logger.info(f'Finished download of {url} -> {filename}')
                return filename
        filename = await asyncio.to_thread(_download_impl)
        if filename:
            self.download_repository.add_downloaded_file(url, filename)
        await self._notify_for_download(url, f'Finished download for {url}')
        self.download_repository.delete_completion_for_url(url)

    async def _download_streamlink(self, url: str, notify: bool, event: threading.Event):
        if notify:
            await self._notify_for_download(url, f'Started streamlink download of <{url}>')
        video_info = await asyncio.to_thread(self.downloader.get_info, url) # Use downloader's get_info
        video_time = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        video_title = yt_dlp.utils.sanitize_filename(video_info.get('title', ''))
        video_id = video_info.get('id', '')
        def get_filepath(parentdir, extension):
            return os.path.join(parentdir, f"{video_title}_{video_id}_{video_time}.{extension}")
        ytdlp_home_dir = config.yt_dlp_config.get("paths", {}).get("home", "./")
        ytdlp_tmp_dir = config.yt_dlp_config.get("paths", {}).get("temp", ytdlp_home_dir)
        streamlink_output = get_filepath(ytdlp_tmp_dir, "ts")
        logger.info(f"Downloading to {streamlink_output}")
        args = [config.streamlink_config.executable,
                url,
                config.streamlink_config.resolution,
                "-o", streamlink_output,
                *config.streamlink_config.extra_args]
        logger.info(f"Streamlink cmd: {args}")

        proc = await asyncio.create_subprocess_exec(
            *args)
        result = await proc.wait()
        logger.info(f"Process returned result {result}")

        ffmpeg_output = get_filepath(ytdlp_home_dir, "mp4")

        ffmpeg_convert_args = ['ffmpeg', '-i', streamlink_output, '-c:v', 'copy', '-c:a', 'copy', ffmpeg_output]
        logger.info(f'ffmpeg muxing ts: {ffmpeg_convert_args}')
        proc = await asyncio.create_subprocess_exec(*ffmpeg_convert_args)
        result = await proc.wait()
        if proc.returncode == 0:
            logger.info(f'ffmpeg success, removing {streamlink_output}')
            os.remove(streamlink_output)
            self.download_repository.add_downloaded_file(url, ffmpeg_output)
            
        await self._notify_for_download(url, f'Finished download for {url}')
        self.download_repository.delete_completion_for_url(url)

    def create_download_task(self, url: str, notify: bool, extra_args: dict, streamlink: bool):
        event = threading.Event()
        if streamlink:
            task = asyncio.create_task(self._download_streamlink(url, notify, event))
        else:
            task = asyncio.create_task(self._download(url, notify, extra_args, event))
        return DownloadTask(task, event)

    async def start_download(self, url: str, guild_id=None, channel_id=None, notify=False, streamlink=False, extra_args: dict = None):
        if guild_id and channel_id:
            self.download_repository.add_completion_for_url(guild_id, channel_id, url)
        task = self.create_download_task(url, notify, extra_args or {}, streamlink)
        self.current_downloads[url] = task

    def get_running_downloads(self):
        return self.current_downloads.keys()

    def cancel_download(self, url):
        if url in self.current_downloads:
            logger.info(f'Setting event {self.current_downloads[url].event}')
            self.current_downloads[url].event.set()
            return True
        return False
