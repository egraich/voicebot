import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

import config
from handlers import router
import database

logger = logging.getLogger(__name__)

def clear_temp_directory() -> None:
    """Remove all files from the shared temporary directory on startup."""
    if not os.path.exists(config.TEMP_DIR):
        os.makedirs(config.TEMP_DIR, exist_ok=True)
        return
        
    for filename in os.listdir(config.TEMP_DIR):
        file_path = os.path.join(config.TEMP_DIR, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed orphaned file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove orphaned file {file_path}: {e}")

async def main() -> None:
    """Initialize database, cleanup directories and start the bot polling."""
    config.setup_logging()
    logger.info("Initializing VoiceBot v1.1...")
    
    await database.init_db()
    clear_temp_directory()
    
    session = None
    if "api.telegram.org" not in config.BOT_API_URL:
        logger.info(f"Using local Telegram Bot API Server: {config.BOT_API_URL}")
        session = AiohttpSession(
            api=TelegramAPIServer.from_base(config.BOT_API_URL, is_local=True)
        )
        
    bot = Bot(
        token=config.BOT_TOKEN, 
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    dp.include_router(router)
    
    try:
        logger.info("Bot successfully started and listening for updates.")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical startup error: {e}", exc_info=True)
    finally:
        logger.info("Gracefully stopping bot...")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot manually interrupted (Ctrl+C).")