"""
Format conversion handlers for the Telegram bot.
Handles MP3/MP4 conversion and quality adjustments.
"""

from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import AUDIO_QUALITY_PRESETS, VIDEO_QUALITY_PRESETS
from services.converter import convert_to_audio, convert_video_quality, convert_video_to_mp4
from services.extractor import extract_audio
from services.cleanup import generate_temp_filename, secure_delete
from utils.validators import get_file_extension


async def conversion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle format conversion request."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "convert_to_mp3":
        await show_audio_quality_options(query, context, "mp3")
    elif data == "convert_to_mp4":
        await convert_audio_to_mp4(query, context)
    elif data == "action_extract_audio":
        await show_audio_quality_options(query, context, "extract")
    elif data == "action_video_quality":
        await show_video_quality_options(query, context)
    elif data == "action_audio_quality":
        await show_audio_quality_options(query, context, "convert")


async def show_audio_quality_options(query, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None:
    """Show audio quality selection buttons."""
    context.user_data['conversion_mode'] = mode
    
    buttons = []
    for key, preset in AUDIO_QUALITY_PRESETS.items():
        buttons.append([
            InlineKeyboardButton(
                f"🎵 {preset['label']}", 
                callback_data=f"quality_audio_{key}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="action_cancel")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        "🎚️ **Select Audio Quality:**\n\n"
        "Higher quality = larger file size",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def show_video_quality_options(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show video quality selection buttons."""
    buttons = []
    for key, preset in VIDEO_QUALITY_PRESETS.items():
        buttons.append([
            InlineKeyboardButton(
                f"📐 {preset['label']}", 
                callback_data=f"quality_video_{key}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="action_cancel")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        "📐 **Select Video Quality:**\n\n"
        "Higher resolution = larger file size",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quality selection callback."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    pending_file = context.user_data.get('pending_file')
    
    if not pending_file:
        await query.edit_message_text("❌ Session expired. Please upload the file again.")
        return
    
    if data.startswith("quality_audio_"):
        quality = data.replace("quality_audio_", "")
        await process_audio_conversion(query, context, user_id, pending_file, quality)
    elif data.startswith("quality_video_"):
        quality = data.replace("quality_video_", "")
        await process_video_conversion(query, context, user_id, pending_file, quality)


async def process_audio_conversion(query, context, user_id: int, pending_file: dict, quality: str) -> None:
    """Process audio extraction/conversion with selected quality."""
    await query.edit_message_text("⏳ **Processing audio...**\nThis may take a moment.", parse_mode="Markdown")
    
    temp_input = None
    temp_output = None
    
    try:
        # Download the file
        file = await context.bot.get_file(pending_file['file_id'])
        temp_input = generate_temp_filename(user_id, pending_file['filename'])
        await file.download_to_drive(str(temp_input))
        
        # Convert/extract to MP3
        output_name = Path(pending_file['filename']).stem + ".mp3"
        temp_output = generate_temp_filename(user_id, output_name, f"_{quality}")
        
        bitrate = AUDIO_QUALITY_PRESETS.get(quality, AUDIO_QUALITY_PRESETS['medium'])['bitrate']
        await extract_audio(temp_input, temp_output, bitrate)
        
        # Send the converted file
        await query.edit_message_text("📤 **Uploading...**", parse_mode="Markdown")
        
        with open(temp_output, 'rb') as audio_file:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_file,
                filename=output_name,
                caption=f"🎵 Converted to MP3 ({AUDIO_QUALITY_PRESETS[quality]['label']})"
            )
        
        await query.edit_message_text(
            "✅ **Audio conversion complete!**\n\n"
            "Send another file when ready.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ **Conversion failed:**\n`{str(e)}`\n\n"
            "Please try again or send a different file.",
            parse_mode="Markdown"
        )
    finally:
        # Clean up temp files
        if temp_input:
            await secure_delete(temp_input)
        if temp_output:
            await secure_delete(temp_output)
        context.user_data.pop('pending_file', None)
        context.user_data.pop('conversion_mode', None)


async def process_video_conversion(query, context, user_id: int, pending_file: dict, quality: str) -> None:
    """Process video quality conversion with selected quality."""
    await query.edit_message_text("⏳ **Processing video...**\nThis may take a while.", parse_mode="Markdown")
    
    temp_input = None
    temp_output = None
    
    try:
        # Download the file
        file = await context.bot.get_file(pending_file['file_id'])
        temp_input = generate_temp_filename(user_id, pending_file['filename'])
        await file.download_to_drive(str(temp_input))
        
        # Convert video
        output_name = Path(pending_file['filename']).stem + f"_{quality}.mp4"
        temp_output = generate_temp_filename(user_id, output_name)
        
        await convert_video_quality(temp_input, temp_output, quality)
        
        # Check file size (Telegram limit is 50MB for bots)
        file_size = temp_output.stat().st_size
        if file_size > 50 * 1024 * 1024:
            await query.edit_message_text(
                f"❌ **Output file too large!**\n\n"
                f"Size: {file_size / (1024*1024):.1f} MB\n"
                f"Telegram limit: 50 MB\n\n"
                "Try a lower quality setting.",
                parse_mode="Markdown"
            )
            return
        
        # Send the converted file
        await query.edit_message_text("📤 **Uploading...**", parse_mode="Markdown")
        
        with open(temp_output, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_file,
                filename=output_name,
                caption=f"🎬 Converted to {VIDEO_QUALITY_PRESETS[quality]['label']}"
            )
        
        await query.edit_message_text(
            "✅ **Video conversion complete!**\n\n"
            "Send another file when ready.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ **Conversion failed:**\n`{str(e)}`\n\n"
            "Please try again or send a different file.",
            parse_mode="Markdown"
        )
    finally:
        # Clean up temp files
        if temp_input:
            await secure_delete(temp_input)
        if temp_output:
            await secure_delete(temp_output)
        context.user_data.pop('pending_file', None)


async def convert_audio_to_mp4(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert audio file to MP4 with a static image or waveform."""
    await query.edit_message_text(
        "⚠️ **Audio to MP4 Conversion**\n\n"
        "This feature creates a video with a static background from your audio.\n"
        "Currently under development.\n\n"
        "Please try another option.",
        parse_mode="Markdown"
    )
