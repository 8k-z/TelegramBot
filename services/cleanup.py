"""
Secure file cleanup service for the Telegram Media Bot.
Handles secure deletion and temp file management.
"""

import os
import secrets
from pathlib import Path
from typing import Optional
import asyncio
import aiofiles

from config import TEMP_DIR


async def secure_delete(file_path: Path) -> bool:
    """
    Securely delete a file by overwriting with random data before deletion.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        if not file_path.exists():
            return True
            
        # Get file size
        file_size = file_path.stat().st_size
        
        # Overwrite with random data (3 passes for security)
        for _ in range(3):
            async with aiofiles.open(file_path, 'wb') as f:
                # Write random bytes in chunks to avoid memory issues
                chunk_size = min(file_size, 1024 * 1024)  # 1MB chunks
                remaining = file_size
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    await f.write(secrets.token_bytes(write_size))
                    remaining -= write_size
        
        # Delete the file
        file_path.unlink()
        return True
        
    except Exception as e:
        print(f"Error securely deleting {file_path}: {e}")
        # Try normal deletion as fallback
        try:
            file_path.unlink()
            return True
        except:
            return False


async def cleanup_user_temp(user_id: int) -> int:
    """
    Clean up all temporary files for a specific user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Number of files deleted
    """
    user_temp_dir = TEMP_DIR / str(user_id)
    deleted_count = 0
    
    if not user_temp_dir.exists():
        return 0
    
    for file_path in user_temp_dir.iterdir():
        if file_path.is_file():
            if await secure_delete(file_path):
                deleted_count += 1
    
    # Try to remove the user's temp directory if empty
    try:
        user_temp_dir.rmdir()
    except OSError:
        pass  # Directory not empty or other error
    
    return deleted_count


async def cleanup_temp_files(max_age_hours: int = 1) -> int:
    """
    Clean up old temporary files from all users.
    
    Args:
        max_age_hours: Maximum age of files to keep in hours
        
    Returns:
        Number of files deleted
    """
    import time
    
    deleted_count = 0
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    
    if not TEMP_DIR.exists():
        return 0
    
    for user_dir in TEMP_DIR.iterdir():
        if not user_dir.is_dir():
            continue
            
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                try:
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        if await secure_delete(file_path):
                            deleted_count += 1
                except Exception as e:
                    print(f"Error checking file {file_path}: {e}")
        
        # Try to remove empty user directories
        try:
            user_dir.rmdir()
        except OSError:
            pass
    
    return deleted_count


def get_user_temp_dir(user_id: int) -> Path:
    """
    Get or create a temporary directory for a specific user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Path to user's temp directory
    """
    user_temp_dir = TEMP_DIR / str(user_id)
    user_temp_dir.mkdir(parents=True, exist_ok=True)
    return user_temp_dir


def generate_temp_filename(user_id: int, original_filename: str, suffix: Optional[str] = None) -> Path:
    """
    Generate a unique temporary filename for a user.
    
    Args:
        user_id: Telegram user ID
        original_filename: Original file name
        suffix: Optional suffix to add before extension
        
    Returns:
        Path to the temporary file
    """
    user_temp_dir = get_user_temp_dir(user_id)
    original_path = Path(original_filename)
    
    # Generate unique prefix
    unique_prefix = secrets.token_hex(8)
    
    if suffix:
        new_name = f"{unique_prefix}_{original_path.stem}_{suffix}{original_path.suffix}"
    else:
        new_name = f"{unique_prefix}_{original_path.name}"
    
    return user_temp_dir / new_name
