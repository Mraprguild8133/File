import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
import logging

logger = logging.getLogger(__name__)

class TurboDownloader:
    """Turbo-optimized file downloader"""
    
    def __init__(self):
        self.download_queue = asyncio.Queue()
        self.active_downloads = 0

    async def download_file(self, message: Message, status_message: Message):
        """Download file with extreme speed"""
        start_time = time.time()
        
        try:
            file_obj = message.document or message.video or message.audio
            if not file_obj:
                return {'success': False, 'error': 'No file found'}

            file_name = getattr(file_obj, 'file_name', 'file')
            file_size = getattr(file_obj, 'file_size', 0)

            # Create downloads directory
            os.makedirs('downloads', exist_ok=True)
            file_path = os.path.join('downloads', f"temp_{int(time.time())}_{file_name}")

            # Update status
            await status_message.edit_text(
                f"📥 **Turbo Download Starting...**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {self.format_bytes(file_size)}"
            )

            # Download with turbo settings
            downloaded_path = await message.download(
                file_name=file_path,
                progress=self.progress_callback,
                progress_args=(status_message, start_time, "📥 DOWNLOADING"),
                chunk_size=Config.CHUNK_SIZE,
                max_connections=4
            )

            if downloaded_path and os.path.exists(downloaded_path):
                download_time = time.time() - start_time
                speed = file_size / download_time if download_time > 0 else 0
                
                logger.info(f"Download completed: {file_name} in {download_time:.1f}s")
                
                return {
                    'success': True, 
                    'file_path': downloaded_path,
                    'file_name': file_name,
                    'download_time': download_time,
                    'speed': speed
                }
            else:
                return {'success': False, 'error': 'Download failed'}

        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'success': False, 'error': str(e)}

    async def progress_callback(self, current, total, status_message, start_time, action):
        """Optimized progress callback"""
        if total == 0:
            return

        elapsed = time.time() - start_time
        percent = (current / total) * 100
        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        # Update every 5% or 3 seconds to reduce API calls
        if int(percent) % 5 == 0 or elapsed % 3 < 0.1:
            bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
            
            text = (
                f"**{action}**\n\n"
                f"`{bar}`\n"
                f"**Progress:** {percent:.1f}%\n"
                f"**Speed:** {self.format_bytes(speed)}/s\n"
                f"**ETA:** {int(eta)}s"
            )
            
            try:
                await status_message.edit_text(text)
            except:
                pass

    def format_bytes(self, size):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
