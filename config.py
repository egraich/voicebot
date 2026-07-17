import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("Критическая ошибка: BOT_TOKEN или GROQ_API_KEY не найдены в .env!")


MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
GROQ_MODEL = "whisper-large-v3"
TEMP_DIR = "temp_media"

class UI:
    START_MESSAGE = (
        "👋 <b>Привет! Я VoiceBot.</b>\n\n"
        "Просто перешли мне или отправь:\n"
        "🎤 Голосовое сообщение\n"
        "📹 Видео или Кружочек\n\n"
        "Я моментально расшифрую речь в текст с помощью ИИ!"
    )
    
    PROCESSING = "⏳ <i>Слушаю и расшифровываю...</i>"
    
    SUCCESS_TITLE = "💬 <b>Текст расшифрован!</b>"
    
    FILE_TOO_BIG = f"❌ Файл слишком большой! Пожалуйста, отправляйте файлы до {MAX_FILE_SIZE_MB} МБ."
    
    ERROR_GENERIC = "⚠️ Произошла ошибка при обработке файла. Попробуйте позже."
    
    BTN_SHOW = "Показать текст"
    BTN_HIDE = "Скрыть текст"

def setup_logging():
    """
    Настраивает продвинутое логирование с таймстампами и уровнями доступа.
    Формат: [Дата Время] УРОВЕНЬ [Файл:Строка] Сообщение
    """
    log_format = "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),

        ]
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)