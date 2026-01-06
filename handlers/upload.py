"""
File upload handlers for the Telegram bot.
Handles document, video, and audio uploads with rights confirmation.
"""

from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import SUPPORTED_FORMATS, COPYRIGHT_REMINDER, MAX_FILE_SIZE_MB
from utils.validators import validate_file_format, validate_file_size, get_file_extension
from services.cleanup import generate_temp_filename


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document file uploads."""
    document = update.message.document
    await _process_upload(update, context, document.file_name, document.file_size, document.file_id)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video file uploads."""
    video = update.message.video
    filename = video.file_name or f"video_{video.file_unique_id}.mp4"
    await _process_upload(update, context, filename, video.file_size, video.file_id)


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle audio file uploads."""
    audio = update.message.audio
    filename = audio.file_name or f"audio_{audio.file_unique_id}.mp3"
    await _process_upload(update, context, filename, audio.file_size, audio.file_id)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice message uploads."""
    voice = update.message.voice
    filename = f"voice_{voice.file_unique_id}.ogg"
    await _process_upload(update, context, filename, voice.file_size, voice.file_id)


async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video note (circle video) uploads."""
    video_note = update.message.video_note
    filename = f"video_note_{video_note.file_unique_id}.mp4"
    await _process_upload(update, context, filename, video_note.file_size, video_note.file_id)


async def _process_upload(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    filename: str,
    file_size: int,
    file_id: str
) -> None:
    """
    Process an uploaded file.
    Validates the file and prompts for rights confirmation.
    """
    user_id = update.effective_user.id
    
    # Validate file format
    if not validate_file_format(filename):
        ext = get_file_extension(filename)
        supported = ", ".join(SUPPORTED_FORMATS)
        await update.message.reply_text(
            f"❌ **Unsupported file format:** `{ext}`\n\n"
            f"Supported formats: {supported}",
            parse_mode="Markdown"
        )
        return
    
    # Validate file size
    if not validate_file_size(file_size):
        await update.message.reply_text(
            f"❌ **File too large!**\n\n"
            f"Maximum file size: {MAX_FILE_SIZE_MB} MB\n"
            f"Your file: {file_size / (1024*1024):.1f} MB",
            parse_mode="Markdown"
        )
        return
    
    # Store file info in context for later use
    context.user_data['pending_file'] = {
        'file_id': file_id,
        'filename': filename,
        'file_size': file_size,
    }
    
    # Create rights confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ I confirm", callback_data="rights_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="rights_cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    confirmation_message = (
        f"📁 **File received:** `{filename}`\n"
        f"📊 **Size:** {file_size / (1024*1024):.1f} MB\n\n"
        f"⚠️ **Rights Confirmation Required**\n\n"
        "Before processing, please confirm that:\n"
        "• You own this content, OR\n"
        "• You have explicit permission to use it\n\n"
        "Do you confirm you have the rights to this content?"
    )
    
    await update.message.reply_text(
        confirmation_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def rights_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle rights confirmation - user confirmed they have rights."""
    query = update.callback_query
    await query.answer()
    
    pending_file = context.user_data.get('pending_file')
    if not pending_file:
        await query.edit_message_text("❌ Session expired. Please upload the file again.")
        return
    
    filename = pending_file['filename']
    ext = get_file_extension(filename)
    
    # Determine available actions based on file type
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv']
    audio_extensions = ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']
    
    is_video = ext in video_extensions
    is_audio = ext in audio_extensions
    
    # Build action buttons
    buttons = [
        [InlineKeyboardButton("📊 Get Metadata", callback_data="action_metadata")]
    ]
    
    if is_video:
        buttons.append([
            InlineKeyboardButton("🎵 Extract Audio", callback_data="action_extract_audio")
        ])
        buttons.append([
            InlineKeyboardButton("🔄 Convert to MP3", callback_data="convert_to_mp3")
        ])
        buttons.append([
            InlineKeyboardButton("📐 Change Quality", callback_data="action_video_quality")
        ])
    
    if is_audio:
        buttons.append([
            InlineKeyboardButton("🔄 Convert to MP4", callback_data="convert_to_mp4")
        ])
        buttons.append([
            InlineKeyboardButton("🎚️ Change Quality", callback_data="action_audio_quality")
        ])
    
    buttons.append([
        InlineKeyboardButton("💾 Save to Storage", callback_data="action_save"),
        InlineKeyboardButton("❌ Cancel", callback_data="action_cancel")
    ])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        f"✅ **Rights confirmed!**\n\n"
        f"📁 **File:** `{filename}`\n\n"
        f"What would you like to do?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def rights_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle rights confirmation cancellation."""
    query = update.callback_query
    await query.answer()
    
    # Clear pending file
    context.user_data.pop('pending_file', None)
    
    await query.edit_message_text(
        "❌ **Operation cancelled.**\n\n"
        f"{COPYRIGHT_REMINDER}",
        parse_mode="Markdown"
    )


async def action_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle action cancellation."""
    query = update.callback_query
    await query.answer()
    
    # Clear pending file
    context.user_data.pop('pending_file', None)
    
    await query.edit_message_text(
        "✅ **Operation cancelled.**\n\n"
        "Send another file when you're ready!",
        parse_mode="Markdown"
    )
