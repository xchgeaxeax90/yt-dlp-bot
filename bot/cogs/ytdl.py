import logging
import discord
from discord.ext import commands, tasks
from bot.downloader import downloader
from bot.helpers import config
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

    @tasks.loop(seconds=config.polling_interval_s, reconnect=True)
    async def check_tasks(self):
        await self.downloader.schedule_deferred_downloads(config.polling_interval_s)
