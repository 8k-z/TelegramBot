"""
Metadata and audio extraction service using FFprobe/FFmpeg.
"""

import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional


async def extract_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a media file using FFprobe.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Dictionary containing metadata information
    """
    try:
        # Run ffprobe to get media info
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFprobe error: {stderr.decode()}")
        
        data = json.loads(stdout.decode())
        
        # Parse and format the metadata
        metadata = {
            "filename": file_path.name,
            "format": data.get("format", {}).get("format_long_name", "Unknown"),
            "duration": format_duration(float(data.get("format", {}).get("duration", 0))),
            "size": format_size(int(data.get("format", {}).get("size", 0))),
            "bitrate": format_bitrate(int(data.get("format", {}).get("bit_rate", 0))),
            "streams": []
        }
        
        # Parse stream information
        for stream in data.get("streams", []):
            stream_info = {
                "type": stream.get("codec_type", "unknown"),
                "codec": stream.get("codec_long_name", stream.get("codec_name", "Unknown")),
            }
            
            if stream.get("codec_type") == "video":
                stream_info["resolution"] = f"{stream.get('width', '?')}x{stream.get('height', '?')}"
                stream_info["fps"] = eval_fps(stream.get("r_frame_rate", "0/1"))
                
            elif stream.get("codec_type") == "audio":
                stream_info["sample_rate"] = f"{stream.get('sample_rate', '?')} Hz"
                stream_info["channels"] = stream.get("channels", "?")
                
            metadata["streams"].append(stream_info)
        
        return metadata
        
    except FileNotFoundError:
        raise Exception("FFprobe not found. Please install FFmpeg.")
    except Exception as e:
        raise Exception(f"Failed to extract metadata: {str(e)}")


async def extract_audio(
    input_path: Path, 
    output_path: Path, 
    bitrate: str = "192k"
) -> Path:
    """
    Extract audio stream from a video file.
    
    Args:
        input_path: Path to the input video file
        output_path: Path for the output audio file
        bitrate: Audio bitrate (e.g., "192k")
        
    Returns:
        Path to the extracted audio file
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-ab', bitrate,
            '-y',  # Overwrite output
            str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode()}")
        
        return output_path
        
    except FileNotFoundError:
        raise Exception("FFmpeg not found. Please install FFmpeg.")
    except Exception as e:
        raise Exception(f"Failed to extract audio: {str(e)}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS format."""
    if seconds <= 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_size(bytes_size: int) -> str:
    """Format file size in human-readable format."""
    if bytes_size <= 0:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    
    return f"{bytes_size:.1f} TB"


def format_bitrate(bps: int) -> str:
    """Format bitrate in human-readable format."""
    if bps <= 0:
        return "Unknown"
    
    kbps = bps / 1000
    if kbps >= 1000:
        return f"{kbps/1000:.1f} Mbps"
    return f"{kbps:.0f} kbps"


def eval_fps(fps_string: str) -> str:
    """Evaluate FPS from fraction string (e.g., '30/1')."""
    try:
        if '/' in fps_string:
            num, den = map(int, fps_string.split('/'))
            if den > 0:
                return f"{num/den:.2f} fps"
        return f"{float(fps_string):.2f} fps"
    except:
        return "Unknown"


def format_metadata_message(metadata: Dict[str, Any]) -> str:
    """
    Format metadata dictionary into a readable Telegram message.
    
    Args:
        metadata: Metadata dictionary from extract_metadata
        
    Returns:
        Formatted string for Telegram
    """
    lines = [
        "📊 **File Metadata**",
        "",
        f"📁 **Filename:** `{metadata['filename']}`",
        f"📦 **Format:** {metadata['format']}",
        f"⏱️ **Duration:** {metadata['duration']}",
        f"💾 **Size:** {metadata['size']}",
        f"📈 **Bitrate:** {metadata['bitrate']}",
        "",
        "**Streams:**"
    ]
    
    for i, stream in enumerate(metadata.get("streams", []), 1):
        stream_type = stream.get("type", "unknown").capitalize()
        codec = stream.get("codec", "Unknown")
        
        if stream.get("type") == "video":
            lines.append(
                f"  🎬 **{stream_type} #{i}:** {codec}\n"
                f"      Resolution: {stream.get('resolution', '?')}\n"
                f"      FPS: {stream.get('fps', '?')}"
            )
        elif stream.get("type") == "audio":
            lines.append(
                f"  🔊 **{stream_type} #{i}:** {codec}\n"
                f"      Sample Rate: {stream.get('sample_rate', '?')}\n"
                f"      Channels: {stream.get('channels', '?')}"
            )
        else:
            lines.append(f"  📎 **{stream_type} #{i}:** {codec}")
    
    return "\n".join(lines)
