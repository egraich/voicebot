import os
import uuid
import time
import logging
import asyncio
from datetime import datetime, UTC
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command

import config
import services
import keyboards
import database

router = Router()
logger = logging.getLogger(__name__)

_semaphore = None

def get_semaphore() -> asyncio.Semaphore:
    """Get or create asyncio semaphore."""
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)
    return _semaphore

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle incoming start commands."""
    await message.answer(config.UI.START_MESSAGE, parse_mode="HTML")

@router.message(Command("db"), F.chat.type == "private", F.from_user.id == config.ADMIN_ID)
async def cmd_send_db(message: Message) -> None:
    """Deliver database file to the authorized administrator."""
    if os.path.exists(config.DB_PATH):
        await message.answer_document(FSInputFile(config.DB_PATH))
    else:
        await message.answer(config.UI.DB_NOT_FOUND)

@router.message(F.voice | F.video | F.video_note | F.audio | F.document)
async def handle_media(message: Message, bot: Bot) -> None:
    """Download, convert and transcribe incoming media files."""
    file_id = None
    is_video = False
    file_type = ""
    duration = 0
    
    if message.voice:
        file_id = message.voice.file_id
        file_size = message.voice.file_size
        file_type = "voice"
        duration = message.voice.duration
    elif message.video_note:
        file_id = message.video_note.file_id
        file_size = message.video_note.file_size
        file_type = "video_note"
        duration = message.video_note.duration
        is_video = True
    elif message.video:
        file_id = message.video.file_id
        file_size = message.video.file_size
        file_type = "video"
        duration = message.video.duration
        is_video = True
    elif message.audio:
        file_id = message.audio.file_id
        file_size = message.audio.file_size
        file_type = "audio"
        duration = message.audio.duration
    elif message.document and message.document.mime_type:
        mime = message.document.mime_type
        if mime.startswith('video/') or mime.startswith('audio/'):
            file_id = message.document.file_id
            file_size = message.document.file_size
            file_type = "document"
            is_video = mime.startswith('video/')
    
    if not file_id:
        return

    if file_size and file_size > config.MAX_FILE_SIZE_BYTES:
        await message.reply(config.UI.FILE_TOO_BIG)
        return

    user_id = message.from_user.id
    if user_id != config.ADMIN_ID:
        today_sec = await database.get_user_today_duration(user_id)
        if today_sec + duration > config.DAILY_LIMIT_SECONDS:
            now = datetime.now(UTC)
            sec_to_midnight = 86400 - (now.hour * 3600 + now.minute * 60 + now.second)
            h_left = sec_to_midnight // 3600
            m_left = (sec_to_midnight % 3600) // 60
            
            limit_h = config.DAILY_LIMIT_SECONDS // 3600
            limit_unit = config.UNIT_H if limit_h > 0 else config.UNIT_M
            limit_val = limit_h if limit_h > 0 else config.DAILY_LIMIT_SECONDS // 60
            
            if message.chat.type == "private":
                await message.reply(config.UI.LIMIT_EXCEEDED_PM.format(
                    limit=limit_val, unit=limit_unit, h=h_left, m=m_left
                ))
            else:
                username = message.from_user.username or message.from_user.first_name
                msg = await message.reply(config.UI.LIMIT_EXCEEDED_GROUP.format(username=username))
                
                async def del_msg(m: Message) -> None:
                    await asyncio.sleep(config.MSG_AUTO_DELETE_SECONDS)
                    try:
                        await m.delete()
                    except Exception:
                        pass
                asyncio.create_task(del_msg(msg))
            return

    status_msg = await message.reply(config.UI.PROCESSING, parse_mode="HTML")
    
    async with get_semaphore():
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
                ext = ".mp4" if is_video else ".mp3"

            input_file_path = os.path.join(config.TEMP_DIR, f"input_{unique_id}{ext}")
            audio_file_path = os.path.join(config.TEMP_DIR, f"audio_{unique_id}.flac")
            
            logger.info(f"Downloading file {file_id} from user {message.from_user.id}")
            await bot.download(file=file_info, destination=input_file_path)
            
            if duration == 0:
                duration = await services.get_duration(input_file_path)
                
            target_audio_path = input_file_path
            
            if is_video:
                success = await services.extract_audio(input_file_path, audio_file_path)
                if not success:
                    raise RuntimeError("Audio extraction process failed")
                target_audio_path = audio_file_path
                
            start_time = time.time()
            transcription_text = await services.transcribe_audio(target_audio_path)
            processing_time = round(time.time() - start_time, 2)
            
            if transcription_text:
                cache_key = f"{status_msg.chat.id}_{status_msg.message_id}"
                await database.save_transcription(cache_key, transcription_text)
                
                username = message.from_user.username
                user_display = f"@{username}" if username else message.from_user.first_name
                
                rounded_size_mb = round(file_size / (1024 * 1024), 2)
                
                await database.save_stats(
                    user_id=user_id,
                    file_type=file_type,
                    duration=duration,
                    username=user_display,
                    file_size=rounded_size_mb,
                    processing_time=processing_time
                )
                
                await status_msg.edit_text(
                    text=config.UI.SUCCESS_TITLE,
                    parse_mode="HTML",
                    reply_markup=keyboards.get_show_text_kb(status_msg.message_id)
                )
            else:
                await status_msg.edit_text(config.UI.ERROR_GENERIC)

        except Exception as e:
            logger.error(f"Media processing failed: {e}", exc_info=True)
            await status_msg.edit_text(config.UI.ERROR_GENERIC)
            
        finally:
            if input_file_path and os.path.exists(input_file_path):
                os.remove(input_file_path)
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            logger.info(f"Temporary workspace cleared for {unique_id}.")

@router.callback_query(F.data.startswith("show_"))
async def process_show_text(callback: CallbackQuery) -> None:
    """Display transcription text."""
    msg_id = callback.data.split("_")[1]
    cache_key = f"{callback.message.chat.id}_{msg_id}"
    
    text = await database.get_transcription(cache_key)
    if text:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboards.get_hide_text_kb(int(msg_id))
        )
    else:
        await callback.answer(config.UI.ERR_NOT_FOUND, show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("hide_"))
async def process_hide_text(callback: CallbackQuery) -> None:
    """Hide transcription text."""
    msg_id = callback.data.split("_")[1]
    
    await callback.message.edit_text(
        text=config.UI.SUCCESS_TITLE,
        parse_mode="HTML",
        reply_markup=keyboards.get_show_text_kb(int(msg_id))
    )
    
    await callback.answer()