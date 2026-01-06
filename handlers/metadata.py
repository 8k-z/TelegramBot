"""
Metadata extraction handler for the Telegram bot.
"""

from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from services.extractor import extract_metadata, format_metadata_message
from services.cleanup import generate_temp_filename, secure_delete


async def metadata_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle metadata extraction request."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pending_file = context.user_data.get('pending_file')
    
    if not pending_file:
        await query.edit_message_text("❌ Session expired. Please upload the file again.")
        return
    
    # Show processing message
    await query.edit_message_text("⏳ **Extracting metadata...**", parse_mode="Markdown")
    
    try:
        # Download the file
        file_id = pending_file['file_id']
        filename = pending_file['filename']
        
        file = await context.bot.get_file(file_id)
        temp_path = generate_temp_filename(user_id, filename)
        
        await file.download_to_drive(str(temp_path))
        
        # Extract metadata
        metadata = await extract_metadata(temp_path)
        message = format_metadata_message(metadata)
        
        # Clean up temp file
        await secure_delete(temp_path)
        
        # Clear pending file
        context.user_data.pop('pending_file', None)
        
        await query.edit_message_text(
            message + "\n\n✅ **Done!** Send another file when ready.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        # Clean up on error
        context.user_data.pop('pending_file', None)
        
        await query.edit_message_text(
            f"❌ **Error extracting metadata:**\n`{str(e)}`\n\n"
            "Please try again or send a different file.",
            parse_mode="Markdown"
        )
