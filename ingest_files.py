import os
import re
import sqlite3
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Regex patterns for the two filename types
# Type 1: [Title]_[VideoID]_[Timestamp].mp4
# e.g., 'WON LIVE #31_PAfs4XOHxd0_20251223-110221.mp4'
STREAMLINK_PATTERN = re.compile(r'_([a-zA-Z0-9_-]{11})_\d{8}-\d{6}\.(?:mp4|mkv|webm|ts)$')

# Type 2: [Title] [[VideoID]].mp4
# e.g., 'Hebi SHOWCASE FULL VERSION [Iur-FZq4cdo].mp4'
YTDLP_PATTERN = re.compile(r'\[([a-zA-Z0-9_-]{11})\]\.(?:mp4|mkv|webm|ts)$')

def get_video_id(filename):
    # Try Type 1 (Streamlink)
    match = STREAMLINK_PATTERN.search(filename)
    if match:
        return match.group(1)
    
    # Try Type 2 (yt-dlp)
    match = YTDLP_PATTERN.search(filename)
    if match:
        return match.group(1)
    
    return None

def ingest_directory(db_path, directory):
    if not os.path.exists(directory):
        logger.error(f"Directory not found: {directory}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    abs_dir = os.path.abspath(directory)
    logger.info(f"Scanning directory: {abs_dir}")
    
    added_count = 0
    skipped_count = 0

    for filename in os.listdir(abs_dir):
        # Skip directories
        filepath = os.path.join(abs_dir, filename)
        if not os.path.isfile(filepath):
            continue

        video_id = get_video_id(filename)
        if not video_id:
            logger.debug(f"Could not parse Video ID from: {filename}")
            skipped_count += 1
            continue

        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            # Check if record already exists for this filepath
            cursor.execute("SELECT id FROM downloaded_files WHERE filepath = ?", (filepath,))
            if cursor.fetchone():
                logger.debug(f"File already tracked: {filename}")
                skipped_count += 1
                continue

            # Insert new record
            cursor.execute("""
                INSERT INTO downloaded_files (url, filepath, download_time) 
                VALUES (?, ?, datetime('now'))
            """, (url, filepath))
            logger.info(f"Added: {filename} (ID: {video_id})")
            added_count += 1
        except Exception as e:
            logger.error(f"Error adding {filename}: {e}")

    conn.commit()
    conn.close()
    
    logger.info("--- Ingestion Complete ---")
    logger.info(f"Total files added: {added_count}")
    logger.info(f"Files skipped (unrecognized or already exists): {skipped_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest video files into the bot's database.")
    parser.add_argument("db", help="Path to the SQLite database file (e.g., bot.db)")
    parser.add_argument("dir", help="Directory containing the video files")
    
    args = parser.parse_args()
    ingest_directory(args.db, args.dir)
