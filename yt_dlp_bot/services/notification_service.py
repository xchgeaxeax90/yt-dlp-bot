from abc import ABC, abstractmethod
import discord
from ..helpers import fetch_guild, fetch_channel

class NotificationService(ABC):
    @abstractmethod
    async def notify(self, guild_id: int, channel_id: int, message: str):
        pass

class DiscordNotificationService(NotificationService):
    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def notify(self, guild_id: int, channel_id: int, message: str):
        guild = await fetch_guild(self.bot, guild_id)
        if not guild:
            return
            
        channel = await fetch_channel(guild, channel_id)
        if not channel:
            return
            
        await channel.send(message)
