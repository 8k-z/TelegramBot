"""
Input validation utilities for the Telegram Media Bot.
"""

from pathlib import Path
from config import SUPPORTED_FORMATS, MAX_FILE_SIZE_BYTES


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return Path(filename).suffix.lower()


def validate_file_format(filename: str) -> bool:
    """
    Check if file format is supported.
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        True if format is supported, False otherwise
    """
    ext = get_file_extension(filename)
    return ext in SUPPORTED_FORMATS


def validate_file_size(file_size: int) -> bool:
    """
    Check if file size is within allowed limits.
    
    Args:
        file_size: Size of the file in bytes
        
    Returns:
        True if size is within limits, False otherwise
    """
    return file_size <= MAX_FILE_SIZE_BYTES


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string (e.g., "15.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
