import os
import asyncio
import logging
from groq import AsyncGroq
import config

groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)
logger = logging.getLogger(__name__)

async def extract_audio(input_path: str, output_path: str) -> bool:
    """Extract and convert sound from video files asynchronously."""
    logger.info(f"Running FFmpeg for {input_path}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-y', '-i', input_path,
            '-vn', '-map', '0:a', '-ar', '16000', '-ac', '1', '-c:a', 'flac',
            output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        await process.communicate()
        
        if process.returncode == 0 and os.path.exists(output_path):
            logger.info(f"FFmpeg process finished successfully: {output_path}")
            return True
            
        logger.error(f"FFmpeg failed with exit code: {process.returncode}")
        return False
            
    except Exception as e:
        logger.error(f"FFmpeg execution exception: {e}")
        return False

async def get_duration(file_path: str) -> int:
    """Read duration using ffprobe checking both format and streams."""
    try:
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration:stream=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0 and stdout:
            lines = stdout.decode().strip().splitlines()
            for line in lines:
                val = line.strip()
                if val and val != "N/A":
                    try:
                        return int(float(val))
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Failed to extract duration: {e}")
    return 0

async def transcribe_audio(audio_path: str) -> str | None:
    """Send audio to Groq API and return the parsed response."""
    logger.info(f"Sending audio file to Groq API: {audio_path}")
    
    try:
        with open(audio_path, "rb") as file:
            transcription = await groq_client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model=config.GROQ_MODEL,
                response_format="json",
                temperature=0.0
            )
        
        result_text = transcription.text.strip() if transcription.text else None
        logger.info(f"Groq API returned payload of length: {len(result_text) if result_text else 0}")
        return result_text
        
    except Exception as e:
        logger.error(f"Groq API connection error: {e}")
        return None