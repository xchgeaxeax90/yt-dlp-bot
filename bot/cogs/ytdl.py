import logging
import discord
from discord.ext import commands, tasks
from bot.downloader import downloader
import sys


logger = logging.getLogger(__name__)

class YtDl(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.hybrid_command(
        name="download",
        brief="Downloads a video or stream asynchronously",
        description="Downloads a video or schedules a download in the future",
        usage="",
        help="Example: y!download https://www.youtube.com/watch?v=e6DSdJ9r-FM"
    )
    async def download(self, ctx: commands.Context, url: str):
        availability = downloader.get_availability(url)
        logger.info(f"Got availability {availability}")
        match availability:
            case downloader.AvailabilityError(errstr):
                await ctx.send(errstr)
            case downloader.AvailableNow:
                await ctx.send("Downloading video now")
            case downloader.AvailableFuture(time):
                formatted_dt = discord.utils.format_dt(time, style='F')
                await ctx.send(f"Scheduling download for {formatted_dt}")
