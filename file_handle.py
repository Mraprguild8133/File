import time
import asyncio
import aiofiles
from pyrogram.types import Message
from config import Config
from PIL import Image
import os
from concurrent.futures import ThreadPoolExecutor

# Thread pool for CPU-intensive operations
thread_pool = ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_DOWNLOADS)

class TurboFileHandler:
    def __init__(self):
        self.download_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_DOWNLOADS)
        self.upload_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_UPLOADS)
        self.thumbnail = self._load_thumbnail()
    
    def _load_thumbnail(self):
        """Load and optimize custom thumbnail"""
        if os.path.exists(Config.CUSTOM_THUMBNAIL):
            try:
                with Image.open(Config.CUSTOM_THUMBNAIL) as img:
                    img.thumbnail(Config.THUMBNAIL_SIZE)
                    return Config.CUSTOM_THUMBNAIL
            except Exception as e:
                print(f"Thumbnail loading failed: {e}")
        return None

async def download_file_turbo(message: Message, status_message: Message):
    """Turbo-optimized file download with progress tracking"""
    start_time = time.time()
    
    async with TurboFileHandler().download_semaphore:
        try:
            file_to_download = message.document or message.video or message.audio
            if not file_to_download:
                await status_message.edit_text("❌ No downloadable file found")
                return None

            # Use larger chunks for faster download
            file_path = await message.download(
                progress=_turbo_progress_callback,
                progress_args=(status_message, start_time, "⚡ DOWNLOADING"),
                chunk_size=Config.CHUNK_SIZE * 4  # Larger chunks for speed
            )
            
            return file_path
        except Exception as e:
            await status_message.edit_text(f"❌ Download failed: {str(e)}")
            return None

async def upload_file_turbo(client, chat_id, file_path, status_message: Message, caption=""):
    """Turbo-optimized file upload with custom thumbnail"""
    start_time = time.time()
    handler = TurboFileHandler()
    
    async with handler.upload_semaphore:
        try:
            # Prepare thumbnail
            thumb = handler.thumbnail if os.path.exists(handler.thumbnail or "") else None
            
            # Optimize upload parameters for speed
            upload_kwargs = {
                'chat_id': chat_id,
                'document': file_path,
                'caption': caption,
                'progress': _turbo_progress_callback,
                'progress_args': (status_message, start_time, "🚀 UPLOADING"),
                'thumb': thumb,
                'chunk_size': Config.CHUNK_SIZE * 4,  # Larger chunks
                'disable_notification': True  # Faster without notifications
            }
            
            await client.send_document(**upload_kwargs)
            await status_message.delete()
            
        except Exception as e:
            await status_message.edit_text(f"❌ Upload failed: {str(e)}")

async def _turbo_progress_callback(current, total, status_message: Message, start_time, action):
    """Optimized progress callback with minimal overhead"""
    if total == 0:
        return
        
    elapsed = time.time() - start_time
    speed = current / elapsed if elapsed > 0 else 0
    percentage = (current / total) * 100
    
    # Update only every 2% or 2 seconds to reduce API calls
    if int(percentage) % 2 == 0 or elapsed % 2 < 0.1:
        progress_bar = "▓" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
        eta = (total - current) / speed if speed > 0 else 0
        
        progress_text = (
            f"**{action}**\n\n"
            f"`{progress_bar}`\n"
            f"**Progress:** {percentage:.1f}%\n"
            f"**Speed:** {_format_bytes(speed)}/s\n"
            f"**ETA:** {int(eta)}s | **Elapsed:** {int(elapsed)}s\n"
            f"`{_format_bytes(current)} / {_format_bytes(total)}`"
        )
        
        try:
            if status_message.text != progress_text:
                await status_message.edit_text(progress_text)
        except Exception:
            pass  # Silent fail to avoid breaking the process

def _format_bytes(size):
    """Ultra-fast bytes formatting"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"
