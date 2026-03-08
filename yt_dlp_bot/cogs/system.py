import logging
import discord
from discord.ext import commands
import shutil
import os
from yt_dlp_bot.repositories.download_repository import DownloadRepository
from yt_dlp_bot.helpers import Config
from yt_dlp_bot.views import PaginatedView
from yt_dlp_bot.services.downloader import Downloader
from yt_dlp_bot.services.download_service import DownloadService, parse_text_duration_timedelta
import datetime

logger = logging.getLogger(__name__)

class DownloadedFileListView(PaginatedView):
    def __init__(self, items: list, format_size_func, items_per_page: int = 10):
        super().__init__(items, items_per_page)
        self.format_size = format_size_func

    async def create_embed(self, page_items: list) -> discord.Embed:
        embed = discord.Embed(
            title=f"Tracked Downloaded Files (Page {self.current_page + 1}/{self.total_pages})",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        lines = []
        for file_id, url, filepath, download_time, is_public, last_check in page_items:
            filename = os.path.basename(filepath)
            # Escape square brackets for markdown link [text](url)
            escaped_name = filename.replace("[", "\\[").replace("]", "\\]")
            truncated_name = (escaped_name[:37] + "...") if len(escaped_name) > 40 else escaped_name
            
            size_str = "N/A"
            if os.path.exists(filepath):
                size_str = self.format_size(os.path.getsize(filepath))
            
            private_str = " [Private]" if is_public == 0 else ""
            lines.append(f"**ID: {file_id}** | [{truncated_name}]({url}){private_str} | {size_str}")

        embed.description = "\n".join(lines) if lines else "No files on this page."
        embed.set_footer(text=f"Total files: {len(self.items)}")
        return embed

class System(commands.Cog):
    def __init__(self, bot, download_repository: DownloadRepository, downloader: Downloader, download_service: DownloadService, config: Config) -> None:
        self.bot = bot
        self.download_repository = download_repository
        self.downloader = downloader
        self.download_service = download_service
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

        view = DownloadedFileListView(files, self._format_size)
        view.update_buttons()
        view.message = await ctx.send(embed=await view.get_current_page_embed(), view=view)

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

    @commands.is_owner()
    @system.command(name="purge", brief="Purges database records for missing files")
    async def purge_files(self, ctx: commands.Context):
        files = self.download_repository.get_downloaded_files()
        purged_count = 0
        for file_id, url, filepath, download_time, is_public, last_check in files:
            if not os.path.exists(filepath):
                self.download_repository.delete_downloaded_file(file_id)
                purged_count += 1
        
        await ctx.send(f"Purged {purged_count} records from the database for missing files.")

    @commands.is_owner()
    @system.command(name="scan", brief="Scans tracked files for availability")
    async def scan_files(self, ctx: commands.Context, include_public: bool = False, older_than: str = None):
        """
        Scans tracked downloaded files to check if the source video is still public.
        
        :param include_public: If True, also scans files already marked as public (is_public=1).
        :param older_than: Optional duration string (e.g., '1w', '2d'). Only scans files checked longer ago than this.
        """
        await ctx.defer()
        files = self.download_repository.get_downloaded_files()
        
        now = datetime.datetime.now(datetime.timezone.utc)
        threshold = None
        if older_than:
            delta = parse_text_duration_timedelta(older_than)
            if delta:
                threshold = now - delta
            else:
                await ctx.send("Invalid duration format. Use e.g., '1w', '2d', '12h'.")
                return

        to_scan = []
        for file_id, url, filepath, download_time, is_public, last_check in files:
            # Filter by is_public status
            if is_public == 1 and not include_public:
                continue
            
            # Filter by last_check duration
            if last_check and threshold:
                # sqlite might return timestamp as string
                try:
                    last_check_dt = datetime.datetime.fromisoformat(last_check).replace(tzinfo=datetime.timezone.utc)
                    if last_check_dt > threshold:
                        continue
                except (ValueError, TypeError):
                    pass # If we can't parse it, we scan it
            
            to_scan.append((file_id, url))

        if not to_scan:
            await ctx.send("No files match the scan criteria.")
            return

        await ctx.send(f"Starting availability scan for {len(to_scan)} files...")
        
        scanned_count = 0
        public_count = 0
        private_count = 0
        
        for file_id, url in to_scan:
            is_available = await self.downloader.check_video_availability(url)
            status_int = 1 if is_available else 0
            self.download_repository.update_downloaded_file_status(file_id, status_int, now.isoformat())
            
            scanned_count += 1
            if is_available:
                public_count += 1
            else:
                private_count += 1
                
        await ctx.send(f"Scan complete. Scanned: {scanned_count}, Still Public: {public_count}, Now Private/Unavailable: {private_count}")
