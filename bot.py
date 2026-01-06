"""
Telegram Media Bot - Main Entry Point

A bot for processing user-provided media files with format conversion,
metadata extraction, and audio extraction capabilities.

Author: Media Bot
License: MIT
"""

import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, COPYRIGHT_REMINDER
from handlers.start import start_command, help_command
from handlers.upload import (
    handle_document,
    handle_video,
    handle_audio,
    handle_voice,
    handle_video_note,
    rights_confirm_callback,
    rights_cancel_callback,
    action_cancel_callback,
)
from handlers.metadata import metadata_callback
from handlers.conversion import conversion_callback, quality_callback
from handlers.storage import (
    files_command,
    delete_command,
    clear_command,
    save_file_callback,
)
from handlers.download import handle_url_message, download_callback
from services.cleanup import cleanup_temp_files

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context) -> None:
    """Handle errors gracefully and remind about copyright."""
    logger.error(f"Exception while handling update: {context.error}")
    
    error_message = (
        "❌ **An error occurred while processing your request.**\n\n"
        "Please try again or send a different file.\n\n"
        f"{COPYRIGHT_REMINDER}"
    )
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                error_message,
                parse_mode="Markdown"
            )
        elif update and update.callback_query:
            await update.callback_query.edit_message_text(
                error_message,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


async def post_init(application: Application) -> None:
    """Perform post-initialization tasks."""
    # Clean up old temp files on startup
    deleted = await cleanup_temp_files(max_age_hours=1)
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} old temporary file(s)")


def main() -> None:
    """Start the bot."""
    # Validate token
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token_here":
        print("=" * 60)
        print("ERROR: Telegram Bot Token not configured!")
        print("=" * 60)
        print()
        print("Please follow these steps:")
        print("1. Create a bot via @BotFather on Telegram")
        print("2. Copy the bot token")
        print("3. Create a .env file with: TELEGRAM_BOT_TOKEN=your_token")
        print()
        print("See .env.example for reference.")
        print("=" * 60)
        sys.exit(1)
    
    print("=" * 60)
    print("  TELEGRAM MEDIA BOT")
    print("=" * 60)
    print()
    print("Starting bot...")
    print()
    print("IMPORTANT REMINDER:")
    print("This bot is for processing files you OWN or have")
    print("EXPLICIT PERMISSION to use. Do not use for copyrighted")
    print("content without authorization.")
    print()
    print("=" * 60)
    
    # Import config for local API settings
    from config import USE_LOCAL_API, LOCAL_API_URL, MAX_FILE_SIZE_MB
    
    # Create the application with local API server if configured
    if USE_LOCAL_API:
        print(f"\n🖥️  Using LOCAL Bot API Server: {LOCAL_API_URL}")
        print(f"📁 Max file size: {MAX_FILE_SIZE_MB} MB")
        print()
        application = (
            Application.builder()
            .token(TELEGRAM_BOT_TOKEN)
            .base_url(LOCAL_API_URL)
            .base_file_url(LOCAL_API_URL.replace("/bot", "/file/bot"))
            .local_mode(True)
            .post_init(post_init)
            .build()
        )
    else:
        print(f"\n☁️  Using Telegram Cloud API")
        print(f"📁 Max file size: {MAX_FILE_SIZE_MB} MB")
        print()
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("files", files_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Add file handlers
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
    
    # Add URL handler for downloads (must be after file handlers)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(rights_confirm_callback, pattern="^rights_confirm$"))
    application.add_handler(CallbackQueryHandler(rights_cancel_callback, pattern="^rights_cancel$"))
    application.add_handler(CallbackQueryHandler(action_cancel_callback, pattern="^action_cancel$"))
    application.add_handler(CallbackQueryHandler(metadata_callback, pattern="^action_metadata$"))
    application.add_handler(CallbackQueryHandler(save_file_callback, pattern="^action_save$"))
    
    # Download callbacks
    application.add_handler(CallbackQueryHandler(download_callback, pattern="^dl_"))
    
    # Conversion callbacks
    application.add_handler(CallbackQueryHandler(conversion_callback, pattern="^convert_"))
    application.add_handler(CallbackQueryHandler(conversion_callback, pattern="^action_extract_audio$"))
    application.add_handler(CallbackQueryHandler(conversion_callback, pattern="^action_video_quality$"))
    application.add_handler(CallbackQueryHandler(conversion_callback, pattern="^action_audio_quality$"))
    application.add_handler(CallbackQueryHandler(quality_callback, pattern="^quality_"))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
