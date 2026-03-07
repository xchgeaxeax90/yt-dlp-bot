import logging
import discord
from discord.ext import commands, tasks
from yt_dlp_bot.helpers import Config

from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.pikl_api.http_client import AsyncHttpClient
from yt_dlp_bot.services.download_service import DownloadService
from yt_dlp_bot.services.scheduler_service import SchedulerService
from typing import Optional

logger = logging.getLogger(__name__)

class YtDl(commands.Cog):
    def __init__(self, bot, http_client: AsyncHttpClient, download_repository: DownloadRepository, download_service: DownloadService, scheduler_service: SchedulerService, config: Config) -> None:
        self.bot = bot
        self.http_client : Optional[AsyncHttpClient] = http_client # Keep this for direct http_client calls in cog
        self.download_repository = download_repository
        self.download_service = download_service
        self.scheduler_service = scheduler_service
        self.config = config

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Starting scheduler service")
        self.scheduler_service.start()

    @commands.is_owner()
    @commands.hybrid_command(
        name="download",
        brief="Downloads a video or stream asynchronously",
        description="Downloads a video or schedules a download in the future",
        usage="",
        help="Example: y!download https://www.youtube.com/watch?v=e6DSdJ9r-FM"
    )
    async def download(self, ctx: commands.Context, url: str):
        await ctx.defer()
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        response_message = await self.download_service.initiate_download(url, guild_id, channel_id)
        await ctx.send(response_message)


    @commands.is_owner()
    @commands.hybrid_command(
        name="scheduled-download",
        brief="Forces a video download at a specific time",
        description="Forces a video download at a specific time",
        usage="",
    )
    async def scheduled_download(self, ctx: commands.Context, url: str, timestamp:str):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        response_message = self.download_service.schedule_download(url, timestamp, guild_id, channel_id)
        await ctx.send(response_message)

    @commands.is_owner()
    @commands.hybrid_command(
        name="streamlink-download",
        brief="Forces a video download through streamlink",
        description="Forces a video download through streamlink",
        usage="",
    )
    async def streamlink_download(self, ctx: commands.Context, url: str):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        response_message = await self.download_service.initiate_download(url, guild_id, channel_id, streamlink=True)
        await ctx.send(f"{response_message} <{url}>")
    
    @commands.is_owner()
    @commands.hybrid_command(
        name="get-running-downloads",
        brief="Gets the currently running downloads",
        description="Gets the currently running downloads",
        usage="",
    )
    async def running_downloads(self, ctx: commands.Context):
        response_message = self.download_service.get_running_downloads()
        await ctx.send(response_message)
    
    @commands.is_owner()
    @commands.hybrid_command(
        name="get-scheduled-downloads",
        brief="Gets the currently scheduled downloads",
        description="Gets the currently scheduled downloads",
        usage="",
    )
    async def scheduled_downloads(self, ctx: commands.Context):
        response_message = self.download_service.get_scheduled_downloads()
        await ctx.send(response_message)

    @commands.is_owner()
    @commands.hybrid_command(
        name="cancel",
        brief="Cancels a download",
        description="Cancels a download",
        usage="",
    )
    async def cancel_download(self, ctx: commands.Context, url: str):
        response_message = self.download_service.cancel_download(url)
        await ctx.send(response_message)




