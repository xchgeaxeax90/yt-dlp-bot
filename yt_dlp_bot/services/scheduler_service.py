import logging
import asyncio
from discord.ext import tasks
import datetime

from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.services.download_manager import DownloadManager
from yt_dlp_bot.helpers import config

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, download_repository: DownloadRepository, download_manager: DownloadManager):
        self.download_repository = download_repository
        self.download_manager = download_manager
        self.running_scheduled_downloads = {} # To keep track of tasks started by the scheduler

    @tasks.loop(seconds=config.polling_interval_s, reconnect=True)
    async def _check_scheduled_downloads(self):
        urls = self.download_repository.get_downloads_now(config.polling_interval_s * 2) # Get downloads scheduled for the next two polling intervals
        [self.download_repository.delete_future_download(url) for url in urls]
        if urls:
            logger.info(f'Scheduler initiating downloads for: {urls}')

        extra_args = {'wait_for_video': [15, 60]}

        # Start asyncio tasks for each video to be downloaded
        new_tasks = {}
        for url in urls:
            # The download_manager.start_download adds the task to its internal current_downloads
            # The scheduler needs to keep its own reference to tasks it initiates for proper management
            await self.download_manager.start_download(url, notify=True, extra_args=extra_args, streamlink=False)
            # We don't directly manage the task here, as DownloadManager already does.
            # But we need to ensure that the DownloadManager's tasks are awaited.
            # For simplicity, we assume DownloadManager manages its lifecycle, and Scheduler just triggers.
            # If a detailed task tracking is needed by the scheduler, DownloadManager should return the task.
            # For now, let's keep track of URLs that were triggered.
            new_tasks[url] = True # Placeholder to indicate it was triggered.

        self.download_repository.cleanup_future_downloads()

        # Clean up completed tasks from DownloadManager (if DownloadManager exposes a way to query)
        # For now, this is implicitly handled by DownloadManager itself.

    def start(self):
        self._check_scheduled_downloads.start()

    def stop(self):
        self._check_scheduled_downloads.cancel()