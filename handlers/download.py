"""
Download handlers for the Telegram bot.
Handles URL-based video downloads from YouTube, Instagram, TikTok, etc.
"""

import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from config import COPYRIGHT_REMINDER, MAX_FILE_SIZE_MB
from services.downloader import (
    get_video_info,
    download_video,
    is_supported_url,
    format_duration,
    format_views,
    get_platform_emoji,
)
from services.cleanup import secure_delete


def safe_text(text: str) -> str:
    """Escape text for Telegram MarkdownV2 format."""
    if not text:
        return "Unknown"
    # Escape special markdown characters
    return escape_markdown(str(text), version=2)


# URL regex pattern
URL_PATTERN = re.compile(
    r'https?://(?:www\.)?'
    r'(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/|'
    r'instagram\.com/(?:p/|reel/|reels/)|'
    r'tiktok\.com/@[\w.-]+/video/|vm\.tiktok\.com/|'
    r'twitter\.com/.+/status/|x\.com/.+/status/|'
    r'facebook\.com/.+/videos/|fb\.watch/|'
    r'vimeo\.com/|'
    r'reddit\.com/r/.+/comments/)'
    r'[\w\-._~:/?#\[\]@!$&\'()*+,;=%]+'
)


async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages containing URLs."""
    text = update.message.text
    
    # Find URLs in the message
    urls = URL_PATTERN.findall(text)
    
    if not urls:
        # Check if it looks like a URL but didn't match
        if 'http' in text.lower() or any(domain in text.lower() for domain in ['youtube', 'instagram', 'tiktok']):
            await update.message.reply_text(
                "🔗 I detected a possible URL, but couldn't parse it.\n\n"
                "Please send a valid link from:\n"
                "• YouTube (videos & shorts)\n"
                "• Instagram (posts & reels)\n"
                "• TikTok\n"
                "• Twitter/X\n"
                "• Facebook\n"
                "• And more!",
                parse_mode="Markdown"
            )
        return
    
    url = urls[0]  # Process first URL
    
    # Store URL in context
    context.user_data['pending_url'] = url
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        "⏳ **Fetching video info...**",
        parse_mode="Markdown"
    )
    
    try:
        # Get video info
        info = await get_video_info(url)
        
        platform_emoji = get_platform_emoji(info['platform'])
        duration = format_duration(info['duration'])
        views = format_views(info['view_count'])
        
        # Store info in context
        context.user_data['video_info'] = info
        
        # Create download options keyboard
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (720p)", callback_data="dl_video_720p"),
                InlineKeyboardButton("🎬 Video (1080p)", callback_data="dl_video_1080p"),
            ],
            [
                InlineKeyboardButton("📱 Video (480p)", callback_data="dl_video_480p"),
                InlineKeyboardButton("📱 Video (360p)", callback_data="dl_video_360p"),
            ],
            [
                InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="dl_audio"),
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="dl_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Escape title and uploader for Markdown
        safe_title = safe_text(info['title'][:100])
        safe_uploader = safe_text(info['uploader'])
        safe_platform = safe_text(info['platform'])
        
        info_message = (
            f"{platform_emoji} *{safe_platform}* Video Found\\!\n\n"
            f"📝 *Title:* {safe_title}\n"
            f"👤 *Uploader:* {safe_uploader}\n"
            f"⏱️ *Duration:* {duration}\n"
            f"👁️ *Views:* {views}\n\n"
            f"⚠️ *Reminder:* Only download content you have rights to use\\.\n\n"
            f"Select download format:"
        )
        
        # Try with MarkdownV2, fallback to plain text
        try:
            await processing_msg.edit_text(
                info_message,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )
        except Exception:
            # Fallback to plain text if Markdown fails
            plain_message = (
                f"{platform_emoji} {info['platform']} Video Found!\n\n"
                f"📝 Title: {info['title'][:100]}\n"
                f"👤 Uploader: {info['uploader']}\n"
                f"⏱️ Duration: {duration}\n"
                f"👁️ Views: {views}\n\n"
                f"⚠️ Reminder: Only download content you have rights to use.\n\n"
                f"Select download format:"
            )
            await processing_msg.edit_text(
                plain_message,
                reply_markup=reply_markup
            )
        
    except Exception as e:
        error_msg = str(e)
        if "Video unavailable" in error_msg or "Private video" in error_msg:
            await processing_msg.edit_text(
                "❌ Video unavailable\n\n"
                "This video might be private, deleted, or region-locked."
            )
        elif "Sign in" in error_msg:
            await processing_msg.edit_text(
                "❌ Login required\n\n"
                "This content requires authentication and cannot be downloaded."
            )
        else:
            # Don't use parse_mode to avoid issues with special characters in error
            await processing_msg.edit_text(
                f"❌ Failed to fetch video info\n\n"
                f"Error: {error_msg[:200]}\n\n"
                "Please try a different URL."
            )


async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle download button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "dl_cancel":
        context.user_data.pop('pending_url', None)
        context.user_data.pop('video_info', None)
        await query.edit_message_text("✅ Download cancelled.")
        return
    
    url = context.user_data.get('pending_url')
    video_info = context.user_data.get('video_info')
    
    if not url:
        await query.edit_message_text("❌ Session expired. Please send the URL again.")
        return
    
    # Parse format and quality from callback data
    if data == "dl_audio":
        format_type = "audio"
        quality = "best"
        format_label = "MP3 Audio"
    else:
        format_type = "video"
        quality = data.replace("dl_video_", "")
        format_label = f"Video ({quality})"
    
    # Show downloading progress
    await query.edit_message_text(
        f"⬇️ Downloading {format_label}...\n\n"
        f"📝 {video_info['title'][:50]}...\n\n"
        "This may take a moment..."
    )
    
    filepath = None
    try:
        # Download the video
        filepath, info = await download_video(url, user_id, format_type, quality)
        
        # Check file size
        file_size = filepath.stat().st_size
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            await query.edit_message_text(
                f"❌ File too large!\n\n"
                f"Size: {file_size / (1024*1024):.1f} MB\n"
                f"Telegram limit: {MAX_FILE_SIZE_MB} MB\n\n"
                "Try a lower quality or audio-only."
            )
            if filepath:
                await secure_delete(filepath)
            return
        
        # Upload to Telegram
        await query.edit_message_text(f"📤 Uploading {format_label}...")
        
        with open(filepath, 'rb') as f:
            if format_type == "audio":
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=f,
                    filename=filepath.name,
                    title=info.get('title', 'Audio')[:64],
                    caption=f"🎵 {info.get('title', 'Audio')[:100]}",
                    read_timeout=1800,  # 30 minutes for large files
                    write_timeout=1800,
                    connect_timeout=60,
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=f,
                    filename=filepath.name,
                    caption=f"🎬 {info.get('title', 'Video')[:100]}",
                    read_timeout=1800,  # 30 minutes for large files
                    write_timeout=1800,
                    connect_timeout=60,
                )
        
        await query.edit_message_text(
            f"✅ Download complete!\n\n"
            f"📝 {info.get('title', 'Media')[:100]}\n\n"
            "Send another URL to download more!"
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ Download failed\n\n"
            f"Error: {str(e)[:200]}\n\n"
            "Please try again or use a different quality."
        )
    finally:
        # Clean up
        if filepath and filepath.exists():
            await secure_delete(filepath)
        context.user_data.pop('pending_url', None)
        context.user_data.pop('video_info', None)
