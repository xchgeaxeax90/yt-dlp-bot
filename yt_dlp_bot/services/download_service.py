import logging
import datetime
import discord
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from yt_dlp_bot.services.download_manager import DownloadManager
from yt_dlp_bot.services.downloader import Downloader, AvailabilityError, AvailableFuture, AvailableNow
from yt_dlp_bot.repositories.download_repository import DownloadRepository

logger = logging.getLogger(__name__)

hammertime_regex = re.compile(r"<t:([0-9]+):?.*>")
time_regex = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_text_duration_timedelta(time_str):
    parts = time_regex.match(time_str)
    if not parts or not any(parts.groups()):
        return None
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params) if time_params else None

class DownloadService:
    def __init__(self, downloader: Downloader, download_repository: DownloadRepository, download_manager: DownloadManager):
        self.downloader = downloader
        self.download_repository = download_repository
        self.download_manager = download_manager

    def parse_text_as_datetime(self, time_text: str) -> Optional[datetime]:
        """Parses either a discord timestamp <t:unixepoch:F> or a human readable string 2d1h5m0s
        as a datetime"""
        if (matches := hammertime_regex.match(time_text)):
            unix_epoch = int(matches.group(1))
            return datetime.fromtimestamp(unix_epoch).astimezone(timezone.utc)
        timedelta_obj = parse_text_duration_timedelta(time_text)
        if not timedelta_obj:
            return None
        return datetime.now().astimezone(timezone.utc) + timedelta_obj

    async def initiate_download(self, url: str, guild_id: int, channel_id: int, streamlink: bool = False, notify: bool = True):
        if streamlink:
            await self.download_manager.start_download(url, guild_id, channel_id, streamlink=True, notify=notify)
            return "Starting streamlink download"

        availability = await self.downloader.get_availability(url)
        match availability:
            case AvailabilityError(errstr):
                return f"Error: {errstr}"
            case AvailableNow():
                await self.download_manager.start_download(url, guild_id, channel_id, notify=notify)
                return "Downloading video now"
            case AvailableFuture(time):
                self.downloader.defer_download_until_time(url, time, guild_id, channel_id)
                formatted_dt = discord.utils.format_dt(time, style='F')
                return f"Scheduling download for {formatted_dt}"
    
    def schedule_download(self, url: str, timestamp_str: str, guild_id: int, channel_id: int):
        time = self.parse_text_as_datetime(timestamp_str)
        if not time:
            return "Invalid timestamp format. Please use <t:unixepoch:F> or a human readable string like 2d1h5m0s."
        self.downloader.defer_download_until_time(url, time, guild_id, channel_id)
        formatted_dt = discord.utils.format_dt(time, style='F')
        return f"Scheduling download for {formatted_dt}"

    def cancel_download(self, url: str):
        if self.download_manager.cancel_download(url):
            return f"Successfully cancelled running download of <{url}>"
        # If not a running download, try to cancel a scheduled download
        if self.downloader.cancel_scheduled_download(url):
            return f"Successfully cancelled scheduled download of <{url}>"
        return f"Could not find <{url}> in running or future downloads"
    
    def get_running_downloads(self):
        urls = self.download_manager.get_running_downloads()
        if not urls:
            return "No downloads currently running."
        msg = "\n".join([f'<{url}>' for url in urls])
        return "Running downloads:\n" + msg

    def get_scheduled_downloads(self):
        results = self.downloader.get_scheduled_downloads()
        if not results:
            return "No downloads currently scheduled."
        lines = []
        for (url, timestamp) in results:
            lines.append(f"<{url}> <t:{int(timestamp)}:F>")
        msg = "\n".join(lines)
        return "Scheduled Downloads:\n" + msg
