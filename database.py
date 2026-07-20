import aiosqlite
import config
from typing import Optional

async def init_db() -> None:
    """Initialize SQLite database with WAL mode and create necessary tables."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute('''
            CREATE TABLE IF NOT EXISTS BUTTON_CASHE(
                msg_key TEXT PRIMARY KEY
                text TEXT NOT NULL
                TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS BOT_STATS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def save_transcription(msg_key: str, text: str) -> None:
    """Save transcription text to cache database and log the action."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO BUTTON_CACHE (msg_key, text) VALUES (?, ?)",
            (msg_key, text)
        )
        await db.execute("INSERT INTO BOT_STATS (action) VALUES (?)", ("transcription_saved",))
        await db.commit()

async def get_transcription(msg_key: str) -> Optional[str]:
    """Retrieve transcription text from cache database by message key."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT text FROM BUTTON_CACHE WHERE msg_key = ?", (msg_key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None