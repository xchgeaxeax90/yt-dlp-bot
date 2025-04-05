import logging
import asyncio
import discord
from discord.ext import commands


from bot import helpers
from bot.bot import YtDlpBot
from bot.cogs import (sync, ytdl)

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

    await bot.add_cog(sync.Sync(bot))
    await bot.add_cog(ytdl.YtDl(bot))
    async with bot:
        await bot.start(helpers.config.discord_key)

if __name__ == '__main__':
    asyncio.run(main())
