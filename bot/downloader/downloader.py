import yt_dlp
import logging
from dataclasses import dataclass

from bot.database import db
from bot.helpers import config
from datetime import datetime

logger = logging.getLogger(__name__)

# Algebraic data type for video availability
@dataclass
class AvailableFuture:
    epoch: datetime

@dataclass
class AvailableNow:
    pass

@dataclass
class AvailabilityError:
    errorstr: str

Availability = AvailableFuture | AvailableNow | AvailabilityError

def get_info(url: str):
    extra_opts = {'ignore_no_formats_error': True}
    with yt_dlp.YoutubeDL(config.yt_dlp_config | extra_opts) as ydl:
        info = ydl.extract_info(url, download=False, process=False)
        return info

def get_availability(url: str) -> Availability:
    try:
        video_info = get_info(url)
        if not 'live_status' in video_info:
            return AvailabilityError('No live status found in video info')
        if video_info['live_status'] == 'is_upcoming':
            # This video is not live yet and must have a download scheduled
            if not 'release_timestamp' in video_info:
                return AvailabilityError('No timestamp found in video info, cannot schedule a download')
            timestamp = int(video_info['release_timestamp'])
            time = datetime.utcfromtimestamp(timestamp)
            return AvailableFuture(time)
        else:
            return AvailableNow
    except Exception as e:
        return AvailabilityError(str(e))




def download(url: str):
    with yt_dlp.YoutubeDL(config.yt_dlp_config) as ydl:
        pass
