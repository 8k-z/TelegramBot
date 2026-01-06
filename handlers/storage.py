"""
File storage management handlers for the Telegram bot.
Allows users to store, list, and delete their files.
"""

import os
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from config import STORAGE_DIR
from services.cleanup import secure_delete


def get_user_storage_dir(user_id: int) -> Path:
    """Get or create a storage directory for a specific user."""
    user_dir = STORAGE_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /files command.
    Lists all files stored for the user.
    """
    user_id = update.effective_user.id
    user_dir = get_user_storage_dir(user_id)
    
    files = list(user_dir.iterdir())
    
    if not files:
        await update.message.reply_text(
            "📁 **Your Storage**\n\n"
            "You don't have any stored files yet.\n\n"
            "Upload a file and select 💾 **Save to Storage** to store it.",
            parse_mode="Markdown"
        )
        return
    
    # Build file list
    file_list = []
    total_size = 0
    
    for i, file_path in enumerate(files, 1):
        if file_path.is_file():
            size = file_path.stat().st_size
            total_size += size
            file_list.append(f"{i}. `{file_path.name}` ({format_file_size(size)})")
    
    message = (
        f"📁 **Your Storage** ({len(file_list)} files)\n"
        f"💾 Total size: {format_file_size(total_size)}\n\n"
        + "\n".join(file_list) +
        "\n\n**Commands:**\n"
        "`/delete <filename>` - Delete a specific file\n"
        "`/clear` - Delete all files"
    )
    
    await update.message.reply_text(message, parse_mode="Markdown")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /delete command.
    Deletes a specific file from user's storage.
    """
    user_id = update.effective_user.id
    user_dir = get_user_storage_dir(user_id)
    
    # Get filename from command arguments
    if not context.args:
        await update.message.reply_text(
            "❌ **Please specify a filename.**\n\n"
            "Usage: `/delete filename.mp3`\n\n"
            "Use `/files` to see your stored files.",
            parse_mode="Markdown"
        )
        return
    
    filename = " ".join(context.args)
    file_path = user_dir / filename
    
    # Security check: ensure file is within user's directory
    try:
        file_path = file_path.resolve()
        user_dir = user_dir.resolve()
        if not str(file_path).startswith(str(user_dir)):
            raise ValueError("Invalid path")
    except:
        await update.message.reply_text(
            "❌ **Invalid filename.**",
            parse_mode="Markdown"
        )
        return
    
    if not file_path.exists():
        await update.message.reply_text(
            f"❌ **File not found:** `{filename}`\n\n"
            "Use `/files` to see your stored files.",
            parse_mode="Markdown"
        )
        return
    
    # Delete the file
    if await secure_delete(file_path):
        await update.message.reply_text(
            f"✅ **File deleted:** `{filename}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ **Failed to delete:** `{filename}`\n\n"
            "Please try again.",
            parse_mode="Markdown"
        )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /clear command.
    Deletes all files from user's storage.
    """
    user_id = update.effective_user.id
    user_dir = get_user_storage_dir(user_id)
    
    files = list(user_dir.iterdir())
    
    if not files:
        await update.message.reply_text(
            "📁 **Your storage is already empty.**",
            parse_mode="Markdown"
        )
        return
    
    deleted_count = 0
    for file_path in files:
        if file_path.is_file():
            if await secure_delete(file_path):
                deleted_count += 1
    
    await update.message.reply_text(
        f"🗑️ **Storage cleared!**\n\n"
        f"Deleted {deleted_count} file(s).",
        parse_mode="Markdown"
    )


async def save_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle save to storage request."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pending_file = context.user_data.get('pending_file')
    
    if not pending_file:
        await query.edit_message_text("❌ Session expired. Please upload the file again.")
        return
    
    await query.edit_message_text("💾 **Saving to storage...**", parse_mode="Markdown")
    
    try:
        # Download the file
        file = await context.bot.get_file(pending_file['file_id'])
        user_dir = get_user_storage_dir(user_id)
        
        # Create unique filename if file already exists
        filename = pending_file['filename']
        save_path = user_dir / filename
        
        counter = 1
        while save_path.exists():
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                save_path = user_dir / f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                save_path = user_dir / f"{filename}_{counter}"
            counter += 1
        
        await file.download_to_drive(str(save_path))
        
        # Clear pending file
        context.user_data.pop('pending_file', None)
        
        await query.edit_message_text(
            f"✅ **File saved!**\n\n"
            f"📁 Filename: `{save_path.name}`\n\n"
            "Use `/files` to see your stored files.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        context.user_data.pop('pending_file', None)
        
        await query.edit_message_text(
            f"❌ **Failed to save file:**\n`{str(e)}`",
            parse_mode="Markdown"
        )
