"""
Media conversion service using FFmpeg.
Handles format conversion and quality adjustments.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable

from config import AUDIO_QUALITY_PRESETS, VIDEO_QUALITY_PRESETS


async def convert_media(
    input_path: Path,
    output_path: Path,
    progress_callback: Optional[Callable] = None
) -> Path:
    """
    Convert media file to a different format.
    
    Args:
        input_path: Path to input file
        output_path: Path for output file (extension determines format)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Path to converted file
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
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
        raise Exception(f"Conversion failed: {str(e)}")


async def convert_to_audio(
    input_path: Path,
    output_path: Path,
    quality: str = "medium",
    output_format: str = "mp3"
) -> Path:
    """
    Convert media file to audio with specified quality.
    
    Args:
        input_path: Path to input file
        output_path: Path for output file
        quality: Quality preset ("low", "medium", "high")
        output_format: Output audio format
        
    Returns:
        Path to converted audio file
    """
    preset = AUDIO_QUALITY_PRESETS.get(quality, AUDIO_QUALITY_PRESETS["medium"])
    bitrate = preset["bitrate"]
    
    try:
        # Determine audio codec based on format
        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "ogg": "libvorbis",
            "flac": "flac",
            "wav": "pcm_s16le"
        }
        codec = codec_map.get(output_format, "libmp3lame")
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-vn',  # No video
            '-acodec', codec,
            '-ab', bitrate,
            '-y',
            str(output_path)
        ]
        
        # FLAC and WAV don't need bitrate
        if output_format in ["flac", "wav"]:
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vn',
                '-acodec', codec,
                '-y',
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
        raise Exception(f"Audio conversion failed: {str(e)}")


async def convert_video_quality(
    input_path: Path,
    output_path: Path,
    quality: str = "720p"
) -> Path:
    """
    Convert video to specified quality/resolution.
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        quality: Quality preset ("480p", "720p", "1080p")
        
    Returns:
        Path to converted video file
    """
    preset = VIDEO_QUALITY_PRESETS.get(quality, VIDEO_QUALITY_PRESETS["720p"])
    resolution = preset["resolution"]
    width, height = resolution.split("x")
    
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',
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
        raise Exception(f"Video conversion failed: {str(e)}")


async def convert_video_to_mp4(
    input_path: Path,
    output_path: Path
) -> Path:
    """
    Convert video to MP4 format with standard settings.
    
    Args:
        input_path: Path to input video
        output_path: Path for output MP4
        
    Returns:
        Path to converted MP4 file
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y',
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
        raise Exception(f"MP4 conversion failed: {str(e)}")
