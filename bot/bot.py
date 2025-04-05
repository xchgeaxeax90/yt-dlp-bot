import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class YtDlpBot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix='y?',
                       intents=intents)
    
