import logging
import discord
from discord.ext import commands
import shutil
import os
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.helpers import Config

logger = logging.getLogger(__name__)

class System(commands.Cog):
    def __init__(self, bot, download_repository: DownloadRepository, config: Config) -> None:
        self.bot = bot
        self.download_repository = download_repository
        self.config = config

    @commands.is_owner()
    @commands.hybrid_group(name="system", brief="System management commands")
    async def system(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @commands.is_owner()
    @system.command(name="df", brief="Gets disk usage of the download directory")
    async def df(self, ctx: commands.Context):
        # Implementation moved from ytdl.py
        if not 'paths' in self.config.yt_dlp_config or not 'home' in self.config.yt_dlp_config['paths']:
            space = shutil.disk_usage('.')
        else:
            space = shutil.disk_usage(self.config.yt_dlp_config['paths']['home'])
        
        await ctx.send(f'Free space {self._format_size(space.free)}')

    def _format_size(self, size_bytes: int) -> str:
        MiB = 1024 * 1024
        GiB = 1024 * MiB
        TiB = 1024 * GiB
        if size_bytes > TiB:
            return f'{size_bytes/TiB:.1f} TiB'
        elif size_bytes > GiB:
            return f'{size_bytes/GiB:.1f} GiB'
        else:
            return f'{size_bytes/MiB:.1f} MiB'

    @commands.is_owner()
    @system.command(name="list", brief="List all tracked downloaded files")
    async def list_files(self, ctx: commands.Context):
        files = self.download_repository.get_downloaded_files()
        if not files:
            await ctx.send("No tracked downloaded files.")
            return

        lines = []
        for file_id, url, filepath, download_time, is_public in files:
            filename = os.path.basename(filepath)
            truncated_name = (filename[:37] + "...") if len(filename) > 40 else filename
            
            size_str = "N/A"
            if os.path.exists(filepath):
                size_str = self._format_size(os.path.getsize(filepath))
            
            lines.append(f"**ID: {file_id}** | `{truncated_name}` | {size_str}")
        
        # Split into chunks if needed (discord message limit is 2000 chars)
        msg = "Tracked downloaded files:\n" + "\n".join(lines)
        if len(msg) > 1900:
            # Simple chunking for now
            for i in range(0, len(msg), 1900):
                await ctx.send(msg[i:i+1900])
        else:
            await ctx.send(msg)

    @commands.is_owner()
    @system.command(name="delete", brief="Deletes a tracked file by ID")
    async def delete_file(self, ctx: commands.Context, file_id: int):
        file_info = self.download_repository.get_downloaded_file_by_id(file_id)
        if not file_info:
            await ctx.send(f"No file found with ID {file_id}")
            return

        filepath = file_info[0]
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                status = f"Deleted file from disk and record {file_id} from database."
            else:
                status = f"File not found on disk, but record {file_id} was removed from database."
            
            self.download_repository.delete_downloaded_file(file_id)
            await ctx.send(status)
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}")
            await ctx.send(f"Error deleting file: {e}")
