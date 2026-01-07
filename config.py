"""
Configuration settings for the Telegram Media Bot.
Loads environment variables and defines constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Local Bot API Server Configuration
# Set to True if running a local Telegram Bot API server
USE_LOCAL_API = os.getenv("USE_LOCAL_API", "true").lower() == "true"
LOCAL_API_URL = os.getenv("LOCAL_API_URL", "http://localhost:8081/bot")

# File size limits
# Cloud API: 50MB max, Local API: 2GB max
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "2000" if USE_LOCAL_API else "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Directory paths
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
STORAGE_DIR = BASE_DIR / "storage"

# Ensure directories exist
TEMP_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)

# Supported formats
SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"]
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"]
SUPPORTED_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS

# Quality presets
AUDIO_QUALITY_PRESETS = {
    "low": {"bitrate": "128k", "label": "128 kbps (Low)"},
    "medium": {"bitrate": "192k", "label": "192 kbps (Medium)"},
    "high": {"bitrate": "320k", "label": "320 kbps (High)"},
}

VIDEO_QUALITY_PRESETS = {
    "480p": {"resolution": "854x480", "label": "480p (SD)"},
    "720p": {"resolution": "1280x720", "label": "720p (HD)"},
    "1080p": {"resolution": "1920x1080", "label": "1080p (Full HD)"},
}

# Cookie settings for yt-dlp (to bypass rate limits)
# Set the browser to extract cookies from, or provide a cookies file path
COOKIES_FROM_BROWSER = os.getenv("COOKIES_FROM_BROWSER", "")  # chrome, firefox, edge, opera, brave (empty = disabled)
COOKIES_FILE = os.getenv("COOKIES_FILE", str(BASE_DIR / "cookies.txt"))  # Path to cookies.txt file (Netscape format)

# Copyright reminder message
COPYRIGHT_REMINDER = (
    "⚠️ **Important Reminder:**\n"
    "This bot is for processing files you **own** or have **explicit permission** to use.\n"
    "Do not use this bot to download or share copyrighted content without authorization.\n"
    "By using this bot, you confirm that you have the necessary rights to the content."
)
