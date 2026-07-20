# VoiceBot

Telegram bot that transcribes voice messages, video notes, audio files, and music into text using Groq's Whisper API.

![VoiceBot Preview](https://raw.githubusercontent.com/username/VoiceBot/main/assets/preview.png)

[Try VoiceBot on Telegram](https://t.me/egvoicebot)

## Quick Start

Send or forward any voice message, video note, audio track, or document to [@egvoicebot](https://t.me/egvoicebot) to receive a transcription.

---

## Features

* Uses Groq `whisper-large-v3` for speech-to-text processing.
* Interactive inline show/hide buttons for output text.
* Supports files up to 2GB via local Telegram Bot API server integration.
* Logs performance metrics and caches transcriptions in SQLite.

---

## How to Run Locally

### Requirements

* Groq API Key
* Telegram Bot Token

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/egraich/VoiceBot.git
   cd VoiceBot
   ```

2. Create a `.env` file inside `VoiceBot/`:
   ```env
   BOT_TOKEN=yout_telegram_bot_token
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ADMIN_ID=your(admin)_id
   TEMP_DIR=path/to/temp/files/directory
   BOT_API_URL=https://api.telegram.org
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Run VoiceBot:
    ```bash
    python main.py
    ```
---

## How It Works

1. **Media Ingestion & Audio Extraction:** Incoming files are downloaded locally. Video files are converted to 16kHz mono FLAC via FFmpeg before sending to the API.
2. **Transcription:** Audio files are transmitted asynchronously to the Groq Cloud API using the `whisper-large-v3` model.
3. **Storage & Local API:** Connecting the bot to a local Telegram Bot API server removes the default 20MB file size ceiling, allowing uploads up to 2000MB. Caching and stats are stored in SQLite database file via `aiosqlite` using `PRAGMA journal_mode=WAL` to handle concurrent operations without database locks.

---

## Credits

* [Aiogram 3](https://github.com/aiogram/aiogram) — Async Telegram Bot API framework.
* [Groq API](https://groq.com/) — Fast speech recognition endpoint.
* [FFmpeg](https://ffmpeg.org/) — Multimedia processing framework.
* [aiosqlite](https://github.com/omnilib/aiosqlite) — Async SQLite driver for Python.