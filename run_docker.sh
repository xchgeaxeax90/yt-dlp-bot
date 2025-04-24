#!/bin/bash

sudo docker run --rm -it -v $(pwd)/runtime:/opt/dl-bot/runtime -v /large/tmp/yt-dlp:/large/tmp/yt-dlp yt-dl-bot python -m yt_dlp_bot.main --config-file /opt/dl-bot/runtime/bot.json --log-level INFO
