import logging
import discord
from discord.ext import commands, tasks
import sys


logger = logging.getLogger(__name__)

class Sync(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.command(
        name="sync",
        brief="Synchronizes the bot's application commands with discord",
        description="Synchronizes the bot's application commands with discord",
        usage="",
        help="Example: t!sync"
    )
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        logger.info("Synchronized application commands")
        await ctx.send(f"Synchronized with discord")

    @commands.is_owner()
    @commands.command(
        name="restart",
        brief="Restarts the bot",
        description="Restarts the bot",
        usage="",
        help="Example: t!restart"
    )
    async def restart(self, ctx: commands.Context):
        logger.info("Restarting the bot")
        await ctx.send(f"Restarting the bot")
        sys.exit(0)

