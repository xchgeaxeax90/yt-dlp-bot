import argparse
import json

def CLI():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', default='INFO', help='Sets the log level')
    parser.add_argument('--config-file', default='bot.json', help='Bot config file location')

    return parser.parse_args()

cli_args = CLI()

def get_config():
    with open(cli_args.config_file, 'r') as f:
        config_data = json.load(f)
        return argparse.Namespace(**config_data)

config = get_config()
