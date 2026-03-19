import logging
import asyncio
import discord
from discord.ext import commands


from yt_dlp_bot import helpers
from yt_dlp_bot.database import init_database
from yt_dlp_bot.services.downloader import Downloader
from yt_dlp_bot.bot import YtDlpBot
from yt_dlp_bot.cogs import (sync, ytdl, subscription, system)
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.repositories.subscription_repository import SubscriptionRepository
from yt_dlp_bot.services.notification_service import DiscordNotificationService
from yt_dlp_bot.services.download_manager import DownloadManager
from yt_dlp_bot.services.download_service import DownloadService
from yt_dlp_bot.services.scheduler_service import SchedulerService
from yt_dlp_bot.services.subscription_service import SubscriptionService


from yt_dlp_bot.pikl_api import waiting_room_client, http_client

logger = logging.getLogger(__name__)

async def main():
    # Set up logging format
    log_format = "%(asctime)s %(levelname)s [%(module)s] (%(funcName)s) - %(message)s"
    logging.basicConfig(level=helpers.cli_args.log_level, format=log_format)
    logging.getLogger("discord").setLevel(logging.INFO)
    logger.info(f"{helpers.config=}")

    intents = discord.Intents()
    intents.guilds = True
    intents.members = False
    intents.message_content = True
    intents.messages = True

    bot = YtDlpBot(
        intents)
        
    con = init_database(helpers.config.database_file)
    download_repository = DownloadRepository(con)
    subscription_repository = SubscriptionRepository(con)
    notification_service = DiscordNotificationService(bot)

    downloader = Downloader(download_repository, subscription_repository, notification_service)
    download_manager = DownloadManager(downloader, download_repository, notification_service)
    download_service = DownloadService(downloader, download_repository, download_manager)
    scheduler_service = SchedulerService(download_repository, download_manager)

    http_client_instance = None
    if helpers.config.pikl_url:
        http_client_instance = http_client.AsyncHttpClient(helpers.config.pikl_url)

    # SubscriptionService needs to be initialized regardless of pikl_url presence
    subscription_service = SubscriptionService(subscription_repository, http_client_instance, download_service, download_repository, helpers.config)

    await bot.add_cog(sync.Sync(bot))
    # Pass all required dependencies to YtDl cog
    await bot.add_cog(ytdl.YtDl(bot, http_client_instance, download_repository, download_service, scheduler_service, helpers.config))
    # Add the new Subscription cog
    await bot.add_cog(subscription.Subscription(bot, http_client_instance, subscription_service, helpers.config))
    # Add the new System cog
    await bot.add_cog(system.System(bot, download_repository, downloader, download_service, helpers.config))
    async with bot:
        tasks = []
        tasks.append(bot.start(helpers.config.discord_key))
        if helpers.config.pikl_url:
            tasks.append(waiting_room_client.run_api_client(helpers.config.pikl_url, subscription_service))

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
