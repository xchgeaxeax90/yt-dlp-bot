import logging
import asyncio
import discord
from discord.ext import commands


from yt_dlp_bot import helpers
from yt_dlp_bot.downloader.downloader import Downloader
from yt_dlp_bot.bot import YtDlpBot
from yt_dlp_bot.cogs import (sync, ytdl)

from yt_dlp_bot.pikl_api import waiting_room_client

logger = logging.getLogger(__name__)

async def main():
    # Set up logging format
    log_format = "%(asctime)s %(levelname)s [%(module)s] (%(funcName)s) - %(message)s"
    logging.basicConfig(level=helpers.cli_args.log_level, format=log_format)
    logging.getLogger("discord").setLevel(logging.INFO)

    intents = discord.Intents()
    intents.guilds = True
    intents.members = False
    intents.message_content = True
    intents.messages = True

    bot = YtDlpBot(
        intents)

    downloader = Downloader(bot)

    http_client = None
    if helpers.config.pikl_url:
        http_client = waiting_room_client.AsyncHttpClient(helpers.config.pikl_url)

    await bot.add_cog(sync.Sync(bot))
    await bot.add_cog(ytdl.YtDl(bot, downloader, http_client))
    async with bot:
        tasks = []
        tasks.append(bot.start(helpers.config.discord_key))
        if helpers.config.pikl_url:
            tasks.append(waiting_room_client.run_api_client(helpers.config.pikl_url, downloader))

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
