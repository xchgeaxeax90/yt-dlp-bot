import logging
import discord
from discord.ext import commands
from yt_dlp_bot.helpers import Config
from yt_dlp_bot.database import RoomKind
from yt_dlp_bot.pikl_api.http_client import AsyncHttpClient
from yt_dlp_bot.services.subscription_service import SubscriptionService # New import

logger = logging.getLogger(__name__)

class Subscription(commands.Cog):
    def __init__(self, bot, http_client: AsyncHttpClient, subscription_service: SubscriptionService, config: Config) -> None:
        self.bot = bot
        self.http_client = http_client
        self.subscription_service = subscription_service
        self.config = config

    @commands.is_owner()
    @commands.hybrid_group(
        name="subscription",
        brief="Commands for managing channel subscriptions",
        description="Commands for managing channel subscriptions",
        usage="",
        fallback="subscribe"
    )
    async def subscription_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @subscription_group.command(
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

    @subscription_group.command(
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
