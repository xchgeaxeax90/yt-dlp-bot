import logging
import discord
from discord.ext import commands, tasks
from yt_dlp_bot.helpers import Config

from yt_dlp_bot.database import RoomKind
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.repositories.subscription_repository import SubscriptionRepository
from yt_dlp_bot.pikl_api.http_client import AsyncHttpClient
from yt_dlp_bot.services.download_service import DownloadService
from yt_dlp_bot.services.scheduler_service import SchedulerService
from yt_dlp_bot.services.subscription_service import SubscriptionService # New import
import shutil
import sys
from typing import Optional

logger = logging.getLogger(__name__)

class YtDl(commands.Cog):
    def __init__(self, bot, http_client: AsyncHttpClient, download_repository: DownloadRepository, subscription_repository: SubscriptionRepository, download_service: DownloadService, scheduler_service: SchedulerService, subscription_service: SubscriptionService, config: Config) -> None:
        self.bot = bot
        self.http_client : Optional[AsyncHttpClient] = http_client # Keep this for direct http_client calls in cog
        self.download_repository = download_repository
        self.subscription_repository = subscription_repository # Re-added
        self.download_service = download_service
        self.scheduler_service = scheduler_service
        self.subscription_service = subscription_service # New
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
        name="df",
        brief="Gets disk usage of the download directory",
        description="Gets disk usage of the download directory",
        usage="",
    )
    async def df(self, ctx: commands.Context):
        if not 'paths' in self.config.yt_dlp_config or not 'home' in self.config.yt_dlp_config['paths']:
            space = shutil.disk_usage('.')
        else:
            space = shutil.disk_usage(self.config.yt_dlp_config['paths']['home'])
        MiB = 1024 * 1024
        GiB = 1024 * MiB
        TiB = 1024 * GiB
        if space.free > TiB:
            msg = f'Free space {space.free/TiB:.1f} TiB'
        elif space.free > GiB:
            msg = f'Free space {space.free/GiB:.1f} GiB'
        else:
            msg = f'Free space {space.free/MiB:.1f} MiB'
        await ctx.send(msg)

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

    @commands.is_owner()
    @commands.hybrid_command(
        name="subscribe",
        brief="Subscribes to automatic downloads for a channel",
        description="Subscribes to automatic downloads for a channel",
        usage="",
    )
    async def subscribe(self, ctx: commands.Context, youtube_channel: str, kind: RoomKind):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        self.subscription_service.subscribe_to_channel(youtube_channel, kind, guild_id, channel_id)
        await self.http_client.subscribe_to_channel(guild_id, youtube_channel)
        await ctx.send(f"Subscribed to automatic {kind.value} downloads from {youtube_channel}")

    @commands.is_owner()
    @commands.hybrid_command(
        name="unsubscribe",
        brief="Unsubscribes from automatic downloads for a channel",
        description="Unsubscribes from automatic downloads for a channel",
        usage="",
    )
    async def unsubscribe(self, ctx: commands.Context, youtube_channel: str, kind: RoomKind | None = None):
        guild_id = ctx.guild.id
        self.subscription_service.unsubscribe_from_channel(youtube_channel, kind, guild_id)
        await self.http_client.unsubscribe_from_channel(guild_id, youtube_channel)
        if kind:
            await ctx.send(f"Unsubscribed to automatic {kind.value} downloads from {youtube_channel}")
        else:
            await ctx.send(f"Unsubscribed to all automatic downloads from {youtube_channel}")


