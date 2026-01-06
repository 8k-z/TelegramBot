# Telegram Media Bot

A Python Telegram bot for processing user-provided media files with format conversion, metadata extraction, and audio extraction capabilities.

## ⚠️ Important Legal Notice

This bot is designed to process **only files you own or have explicit permission to use**. 

**DO NOT** use this bot to:
- Download copyrighted content without permission
- Bypass DRM or platform restrictions
- Share copyrighted material

By using this bot, you confirm you have the necessary rights to all content processed.

## Features

- 📤 **File Upload** - Support for video and audio files
- 📊 **Metadata Extraction** - View detailed file information
- 🎵 **Audio Extraction** - Extract MP3 from video files
- 🔄 **Format Conversion** - Convert between MP3/MP4
- 🎚️ **Quality Options** - Choose bitrate (128/192/320 kbps) or resolution (480p/720p/1080p)
- 💾 **File Storage** - Save files for later access
- 🗑️ **Secure Cleanup** - Auto-delete temp files after processing

## Requirements

- Python 3.9+
- FFmpeg installed and in PATH
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

## Installation

1. **Clone/Download the project**

2. **Install dependencies:**
   ```bash
   cd TelegramMediaBot
   pip install -r requirements.txt
   ```

3. **Install FFmpeg:**
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

4. **Configure the bot:**
   ```bash
   # Copy the example env file
   copy .env.example .env
   
   # Edit .env and add your bot token
   notepad .env
   ```

5. **Run the bot:**
   ```bash
   python bot.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | Detailed help information |
| `/files` | List your stored files |
| `/delete <filename>` | Delete a specific stored file |
| `/clear` | Delete all stored files |

## Supported Formats

**Video:** MP4, AVI, MKV, MOV, WebM, FLV

**Audio:** MP3, WAV, AAC, FLAC, OGG, M4A

## Project Structure

```
TelegramMediaBot/
├── bot.py              # Main entry point
├── config.py           # Configuration
├── handlers/           # Telegram message handlers
│   ├── start.py        # /start and /help commands
│   ├── upload.py       # File upload handling
│   ├── conversion.py   # Format conversion
│   ├── metadata.py     # Metadata extraction
│   └── storage.py      # File management
├── services/           # Core processing services
│   ├── converter.py    # FFmpeg conversion
│   ├── extractor.py    # Metadata/audio extraction
│   └── cleanup.py      # Secure file deletion
├── utils/              # Utility functions
│   └── validators.py   # Input validation
├── temp/               # Temporary files (auto-cleaned)
└── storage/            # User file storage
```

## License

MIT License
