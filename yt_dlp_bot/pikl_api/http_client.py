import httpx

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
