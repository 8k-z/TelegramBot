"""
Start and help command handlers for the Telegram bot.
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import COPYRIGHT_REMINDER


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    Sends welcome message with usage instructions and copyright reminder.
    """
    welcome_message = (
        "🎬 **Welcome to Media Bot!**\n\n"
        "**📥 Download Videos:**\n"
        "Just send me a link from:\n"
        "• YouTube (videos & shorts)\n"
        "• Instagram (reels & posts)\n"
        "• TikTok\n"
        "• Twitter/X\n"
        "• Facebook & more!\n\n"
        "**📤 Or upload a file** to:\n"
        "• 📊 Extract metadata\n"
        "• 🎵 Extract audio (MP3)\n"
        "• 🔄 Convert formats\n\n"
        "**Commands:**\n"
        "`/start` - Show this message\n"
        "`/help` - Detailed help\n"
        "`/files` - Your stored files\n\n"
        f"{COPYRIGHT_REMINDER}"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.
    Provides detailed usage instructions.
    """
    help_message = (
        "📖 **Media Bot Help**\n\n"
        "**How to use:**\n\n"
        "1️⃣ **Upload a media file**\n"
        "   Send any video (MP4, AVI, MKV, etc.) or audio file (MP3, WAV, etc.)\n\n"
        "2️⃣ **Confirm your rights**\n"
        "   You'll be asked to confirm you own the content or have permission\n\n"
        "3️⃣ **Choose an action:**\n"
        "   • 📊 **Metadata** - View file information (duration, codec, etc.)\n"
        "   • 🎵 **Extract Audio** - Get audio from video as MP3\n"
        "   • 🔄 **Convert** - Change format or quality\n"
        "   • 💾 **Save** - Store file for later\n\n"
        "4️⃣ **Select quality** (for conversions)\n"
        "   Audio: 128kbps / 192kbps / 320kbps\n"
        "   Video: 480p / 720p / 1080p\n\n"
        "**File Management:**\n"
        "`/files` - List your saved files\n"
        "`/delete filename` - Delete a specific file\n"
        "`/clear` - Remove all saved files\n\n"
        "**Supported Formats:**\n"
        "🎬 Video: MP4, AVI, MKV, MOV, WebM, FLV\n"
        "🎵 Audio: MP3, WAV, AAC, FLAC, OGG, M4A\n\n"
        f"{COPYRIGHT_REMINDER}"
    )
    
    await update.message.reply_text(
        help_message,
        parse_mode="Markdown"
    )
