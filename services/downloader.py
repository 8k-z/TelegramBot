"""
Video download service using yt-dlp.
Supports YouTube, Instagram, TikTok, and many other platforms.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yt_dlp

from config import TEMP_DIR, MAX_FILE_SIZE_MB, COOKIES_FROM_BROWSER, COOKIES_FILE


def get_cookie_opts() -> dict:
    """Get yt-dlp options for cookie authentication."""
    opts = {}
    
    # Prefer cookies file if provided
    if COOKIES_FILE and Path(COOKIES_FILE).exists():
        opts['cookiefile'] = COOKIES_FILE
    elif COOKIES_FROM_BROWSER:
        opts['cookiesfrombrowser'] = (COOKIES_FROM_BROWSER, None, None, None)
    
    return opts


def get_user_download_dir(user_id: int) -> Path:
    """Get or create a download directory for a specific user."""
    user_dir = TEMP_DIR / str(user_id) / "downloads"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


async def get_video_info(url: str) -> Dict[str, Any]:
    """
    Get video information without downloading.
    
    Args:
        url: Video URL
        
    Returns:
        Dictionary with video metadata
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        **get_cookie_opts(),  # Add cookie support
    }
    
    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, extract)
    
    return {
        'title': info.get('title', 'Unknown'),
        'duration': info.get('duration', 0),
        'uploader': info.get('uploader', 'Unknown'),
        'view_count': info.get('view_count', 0),
        'platform': info.get('extractor', 'Unknown'),
        'thumbnail': info.get('thumbnail'),
        'formats': info.get('formats', []),
        'url': url,
    }


async def download_video(
    url: str,
    user_id: int,
    format_type: str = "best",
    quality: str = "720p"
) -> Tuple[Path, Dict[str, Any]]:
    """
    Download video from URL.
    
    Args:
        url: Video URL
        user_id: Telegram user ID
        format_type: "video", "audio", or "best"
        quality: Video quality (360p, 480p, 720p, 1080p)
        
    Returns:
        Tuple of (file path, video info)
    """
    download_dir = get_user_download_dir(user_id)
    
    # Quality to height mapping
    quality_map = {
        "360p": 360,
        "480p": 480,
        "720p": 720,
        "1080p": 1080,
    }
    max_height = quality_map.get(quality, 720)
    
    # Configure download options based on format type
    if format_type == "audio":
        format_spec = 'bestaudio[ext=m4a]/bestaudio/best'
        ext = 'mp3'
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Video format - limit by height
        format_spec = f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best'
        ext = 'mp4'
        postprocessors = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    
    ydl_opts = {
        'format': format_spec,
        'outtmpl': str(download_dir / '%(title).50s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'postprocessors': postprocessors,
        'max_filesize': MAX_FILE_SIZE_MB * 1024 * 1024,
        'merge_output_format': 'mp4' if format_type != "audio" else None,
        **get_cookie_opts(),  # Add cookie support
    }
    
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual downloaded filename
            if info.get('requested_downloads'):
                filepath = info['requested_downloads'][0]['filepath']
            else:
                filepath = ydl.prepare_filename(info)
                # Handle post-processor extension changes
                if format_type == "audio":
                    filepath = str(Path(filepath).with_suffix('.mp3'))
            return filepath, info
    
    loop = asyncio.get_event_loop()
    filepath, info = await loop.run_in_executor(None, download)
    
    return Path(filepath), {
        'title': info.get('title', 'Unknown'),
        'duration': info.get('duration', 0),
        'uploader': info.get('uploader', 'Unknown'),
        'platform': info.get('extractor', 'Unknown'),
    }


def format_duration(seconds) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if not seconds:
        return "Unknown"
    
    try:
        seconds = int(float(seconds))
    except (ValueError, TypeError):
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_views(count) -> str:
    """Format view count in human-readable format."""
    if not count:
        return "Unknown"
    
    try:
        count = int(float(count))
    except (ValueError, TypeError):
        return "Unknown"
    
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    elif count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def is_supported_url(url: str) -> bool:
    """Check if URL is from a supported platform."""
    supported_domains = [
        'youtube.com', 'youtu.be', 'youtube.com/shorts',
        'instagram.com', 'instagr.am',
        'tiktok.com', 'vm.tiktok.com',
        'twitter.com', 'x.com',
        'facebook.com', 'fb.watch',
        'vimeo.com',
        'dailymotion.com',
        'twitch.tv',
        'reddit.com',
        'soundcloud.com',
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in supported_domains)


def get_platform_emoji(platform: str) -> str:
    """Get emoji for platform."""
    emojis = {
        'youtube': '🔴',
        'instagram': '📸',
        'tiktok': '🎵',
        'twitter': '🐦',
        'facebook': '📘',
        'vimeo': '🎬',
        'twitch': '💜',
        'reddit': '🤖',
        'soundcloud': '🔊',
    }
    
    platform_lower = platform.lower()
    for key, emoji in emojis.items():
        if key in platform_lower:
            return emoji
    return '🎥'
