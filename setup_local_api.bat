@echo off
REM Telegram Bot API Local Server Setup Script for Windows
REM This script downloads and runs the Telegram Bot API server locally

echo ============================================================
echo   Telegram Bot API Local Server Setup
echo ============================================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo Docker found! Starting Telegram Bot API server...
echo.

REM Create data directory
if not exist "telegram-bot-api-data" mkdir telegram-bot-api-data

REM Stop any existing container
docker stop telegram-bot-api 2>nul
docker rm telegram-bot-api 2>nul

REM Run the Telegram Bot API server
docker run -d ^
    --name telegram-bot-api ^
    --restart unless-stopped ^
    -p 8081:8081 ^
    -v "%cd%\telegram-bot-api-data:/var/lib/telegram-bot-api" ^
    -e TELEGRAM_LOCAL=1 ^
    aiogram/telegram-bot-api:latest

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   SUCCESS! Local Bot API server is running.
    echo ============================================================
    echo.
    echo Server URL: http://localhost:8081/bot
    echo Max file size: 2GB
    echo.
    echo You can now run: python bot.py
    echo.
) else (
    echo.
    echo ERROR: Failed to start the container.
    echo.
)

pause
