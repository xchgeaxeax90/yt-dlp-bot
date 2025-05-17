import httpx
import asyncio
import json
import logging
from yt_dlp_bot.database import RoomKind, YoutubeWaitingRoom, YoutubeVideo
from yt_dlp_bot.downloader.downloader import Downloader

logger = logging.getLogger(__name__)

class AsyncSSEClient:
    def __init__(self, url:str, downloader: Downloader, retry_delay: float=30.0):
        self.url = url + "/live?new_only=true"
        self.downloader = downloader
        self.retry_delay = retry_delay
        self.last_event_id = None

    async def connect_and_stream(self, on_event):
        headers = {
            "Accept": "text/event-stream"
        }

        if self.last_event_id:
            headers["Last-Event-ID"] = self.last_event_id

        # TODO: Figure out why this isn't using the retry delay?
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            async with client.stream("GET", self.url, headers=headers) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line.removeprefix("data:").strip()
                        try:
                            data = json.loads(data_str)
                            await on_event(data)
                        except json.JSONDecodeError:
                            logger.warning("invalid json: " + data_str)
                    elif line.startswith("id:"):
                        self.last_event_id = line.removeprefix("id:").strip()
                        
    async def listen(self):
        async def on_event(data):
            await self.handle_event(data)
        while True:
            try:
                logger.info("Connecting to SSE Stream")
                await self.connect_and_stream(on_event)
            except (httpx.RequestError, httpx.HTTPError) as e:
                logger.warning(f"Connection Error {e}")
            except asyncio.CancelledError:
                print("Client cancel")
                break
            logger.info("Attempting to reconnect")
            await asyncio.sleep(self.retry_delay)

    async def handle_event(self, data):
        video = YoutubeVideo(**data)
        logger.info(f"Received {video}")
        await self.downloader.receive_stream_notification(video)
        

async def run_api_client(url: str, downloader: Downloader):
    client = AsyncSSEClient(url, downloader)
    await client.listen()


class AsyncHttpClient:
    def __init__(self, url: str):
        self.url = url
        self.client = httpx.AsyncClient()

    async def subscribe_to_channel(self, guild_id: int, channel_id: str):
        data = {'guild_id': guild_id, 'youtube_channel': channel_id}
        await self.client.put(self.url + '/subscriptions', params=data)

    async def unsubscribe_from_channel(self, guild_id: int, channel_id: str):
        data = {'guild_id': guild_id, 'youtube_channel': channel_id}
        await self.client.delete(self.url + '/subscriptions', params=data)
    
