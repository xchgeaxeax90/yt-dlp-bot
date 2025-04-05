import argparse
import json
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
    yt_dlp_config: dict = {}

def get_config():
    with open(cli_args.config_file, 'r') as f:
        config_data = json.load(f)
        return Config(**config_data)

config = get_config()
