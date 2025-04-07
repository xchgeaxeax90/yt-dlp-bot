import argparse
import json
import discord
import logging
from pydantic import BaseModel

def CLI():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', default='INFO', help='Sets the log level')
    parser.add_argument('--config-file', default='bot.json', help='Bot config file location')

    return parser.parse_args()

cli_args = CLI()

class Config(BaseModel):
    discord_key: str
    database_file: str
    polling_interval_s: int = 60
    yt_dlp_config: dict = {}

def get_config():
    with open(cli_args.config_file, 'r') as f:
        config_data = json.load(f)
        config_data['logger'] = logging.getLogger('yt-dlp')
        return Config(**config_data)

config = get_config()

async def fetch_guild(client, guild_id):
    try:
        if not (channel := client.get_guild(guild_id)):
            channel = await client.fetch_guild(guild_id)
    except discord.errors.NotFound:
        channel = None
    return channel

async def fetch_channel(guild, channel_id):
    try:
        if not (channel := guild.get_channel(channel_id)):
            channel = await guild.fetch_channel(channel_id)
    except discord.errors.NotFound:
        channel = None
    return channel
