import logging
import discord
from discord.ext import commands, tasks
from yt_dlp_bot.downloader import downloader
from yt_dlp_bot.helpers import config
from yt_dlp_bot.database import db, RoomKind
from datetime import datetime, timedelta, timezone
import shutil
import re
import sys


hammertime_regex = re.compile(r"<t:([0-9]+):?.*>")
time_regex = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_text_duration_timedelta(time_str):
    parts = time_regex.match(time_str)
    if not parts:
        return None
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

logger = logging.getLogger(__name__)

class YtDl(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.downloader = downloader.Downloader(self.bot)
        self.check_tasks.start()

    def parse_text_as_datetime(self, time_text: str):
        """Parses either a discord timestamp <t:unixepoch:F> or a human readable string 2d1h5m0s
        as a datetime"""
        if (matches := hammertime_regex.match(time_text)):
            unix_epoch = int(matches.group(1))
            return datetime.fromtimestamp(unix_epoch).astimezone(timezone.utc)
        timedelta = parse_text_duration_timedelta(time_text)
        if not timedelta:
            return None
        return datetime.now().astimezone(timezone.utc)+timedelta

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
        availability = await self.downloader.get_availability(url)
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        logger.info(f"Got availability {availability}")
        match availability:
            case downloader.AvailabilityError(errstr):
                await ctx.send(errstr)
            case downloader.AvailableNow:
                await ctx.send("Downloading video now")
                await self.downloader.download_async(url, guild_id, channel_id)
            case downloader.AvailableFuture(time):
                self.downloader.defer_download_until_time(url, time, guild_id, channel_id)
                formatted_dt = discord.utils.format_dt(time, style='F')
                await ctx.send(f"Scheduling download for {formatted_dt}")


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
        time = self.parse_text_as_datetime(timestamp)
        self.downloader.defer_download_until_time(url, time, guild_id, channel_id)
        formatted_dt = discord.utils.format_dt(time, style='F')
        await ctx.send(f"Scheduling download for {formatted_dt}")
    
    @commands.is_owner()
    @commands.hybrid_command(
        name="df",
        brief="Gets disk usage of the download directory",
        description="Gets disk usage of the download directory",
        usage="",
    )
    async def df(self, ctx: commands.Context):
        if not 'paths' in config.yt_dlp_config or not 'home' in config.yt_dlp_config['paths']:
            space = shutil.disk_usage('.')
        else:
            space = shutil.disk_usage(config.yt_dlp_config['paths']['home'])
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
        urls = self.downloader.get_running_downloads()
        msg = "\n".join([f'<{url}>' for url in urls])
        await ctx.send("Running downloads:\n" + msg)
    
    @commands.is_owner()
    @commands.hybrid_command(
        name="get-scheduled-downloads",
        brief="Gets the currently scheduled downloads",
        description="Gets the currently scheduled downloads",
        usage="",
    )
    async def scheduled_downloads(self, ctx: commands.Context):
        results = self.downloader.get_scheduled_downloads()
        lines = []
        for (url, timestamp) in results:
            lines.append(f"<{url}> <t:{int(timestamp)}:F>")
        msg = "\n".join(lines)
        await ctx.send("Scheduled Downloads:\n" + msg)

    @commands.is_owner()
    @commands.hybrid_command(
        name="cancel",
        brief="Cancels a download",
        description="Cancels a download",
        usage="",
    )
    async def cancel_download(self, ctx: commands.Context, url: str):
        if self.downloader.cancel_download(url):
            await ctx.send(f"Successfully cancelled download of <{url}>")
        else:
            await ctx.send(f"Could not find <{url}> in running or future downloads")

    @commands.is_owner()
    @commands.hybrid_command(
        name="subscribe",
        brief="Subscribes to automatic downloads for a channel",
        description="Subscribes to automatic downloads for a channel",
        usage="",
    )
    async def subscribe(self, ctx: commands.Context, channel_id: str, kind: RoomKind):
        db.subscribe_to_channel(channel_id, kind)
        await ctx.send(f"Subscribed to automatic {kind.value} downloads from {channel_id}")

    @commands.is_owner()
    @commands.hybrid_command(
        name="unsubscribe",
        brief="Unsubscribes from automatic downloads for a channel",
        description="Unsubscribes from automatic downloads for a channel",
        usage="",
    )
    async def unsubscribe(self, ctx: commands.Context, channel_id: str, kind: RoomKind | None = None):
        db.unsubscribe_from_channel(channel_id, kind)
        if kind:
            await ctx.send(f"Unsubscribed to automatic {kind.value} downloads from {channel_id}")
        else:
            await ctx.send(f"Unsubscribed to all automatic downloads from {channel_id}")

    @tasks.loop(seconds=config.polling_interval_s, reconnect=True)
    async def check_tasks(self):
        await self.downloader.schedule_deferred_downloads(config.polling_interval_s)
        db.cleanup_future_downloads()
