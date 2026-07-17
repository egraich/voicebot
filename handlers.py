import os
import uuid
import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import config
import services
import keyboards

router = Router()
logger = logging.getLogger(__name__)

TRANSCRIPTIONS_CACHE = {}

os.makedirs(config.TEMP_DIR, exist_ok=True)

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handles /start message."""
    await message.answer(config.UI.START_MESSAGE, parse_mode="HTML")

@router.message(F.voice | F.video | F.video_note | F.document)
async def handle_media(message: Message, bot: Bot):
    """
    Main handler. Catch media files.
    """
    file_id = None
    is_video = False
    
    if message.voice:
        file_id = message.voice.file_id
        file_size = message.voice.file_size
    elif message.video_note:
        file_id = message.video_note.file_id
        file_size = message.video_note.file_size
        is_video = True
    elif message.video:
        file_id = message.video.file_id
        file_size = message.video.file_size
        is_video = True
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
        file_size = message.document.file_size
        is_video = True
    else:
        return

    if file_size and file_size > config.MAX_FILE_SIZE_BYTES:
        await message.reply(config.UI.FILE_TOO_BIG)
        return

    status_msg = await message.reply(config.UI.PROCESSING, parse_mode="HTML")
    
    unique_id = str(uuid.uuid4())
    input_file_path = None
    audio_file_path = None
    
    try:
        file_info = await bot.get_file(file_id)
        _, ext = os.path.splitext(file_info.file_path)
        ext = ext.lower()

        if ext == ".oga" or message.voice:
            ext = ".ogg"
        elif not ext:
            ext = ".mp4"

        input_file_path = os.path.join(config.TEMP_DIR, f"input_{unique_id}{ext}")
        audio_file_path = os.path.join(config.TEMP_DIR, f"audio_{unique_id}.flac")
        
        logger.info(f"Скачиваем файл {file_id} от пользователя {message.from_user.id}")
        await bot.download(file=file_info, destination=input_file_path)
        
        target_audio_path = input_file_path
        
        if is_video:
            success = await services.extract_audio(input_file_path, audio_file_path)
            if not success:
                raise RuntimeError("Ошибка при извлечении аудио через FFmpeg")
            target_audio_path = audio_file_path
            
        transcription_text = await services.transcribe_audio(target_audio_path)
        
        if transcription_text:
            cache_key = f"{status_msg.chat.id}:{status_msg.message_id}"
            TRANSCRIPTIONS_CACHE[cache_key] = transcription_text
            
            await status_msg.edit_text(
                text=config.UI.SUCCESS_TITLE,
                parse_mode="HTML",
                reply_markup=keyboards.get_show_text_kb(status_msg.message_id)
            )
        else:
            await status_msg.edit_text(config.UI.ERROR_GENERIC)

    except Exception as e:
        logger.error(f"Сбой при обработке медиа: {e}", exc_info=True)
        await status_msg.edit_text(config.UI.ERROR_GENERIC)
        
    finally:
        if input_file_path and os.path.exists(input_file_path):
            os.remove(input_file_path)
        if audio_file_path and os.path.exists(audio_file_path):
            os.remove(audio_file_path)
        logger.info(f"Временные файлы для {unique_id} удалены.")

@router.callback_query(F.data.startswith("show_"))
async def process_show_text(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку [Показать текст]."""
    msg_id = callback.data.split("_")[1]
    cache_key = f"{callback.message.chat.id}:{msg_id}"
    
    text = TRANSCRIPTIONS_CACHE.get(cache_key)
    if text:
        full_message = f"{text}"
        await callback.message.edit_text(
            text=full_message,
            reply_markup=keyboards.get_hide_text_kb(msg_id)
        )
    else:
        await callback.answer("Текст не найден (возможно бот был перезагружен).", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("hide_"))
async def process_hide_text(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку [Скрыть текст]."""
    msg_id = callback.data.split("_")[1]
    
    await callback.message.edit_text(
        text=config.UI.SUCCESS_TITLE,
        parse_mode="HTML",
        reply_markup=keyboards.get_show_text_kb(msg_id)
    )
    
    await callback.answer()