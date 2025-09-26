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

            # Download with progress tracking - CORRECTED SYNTAX
            downloaded_path = await message.download(
                file_name=file_path,
                progress=self.progress_callback,
                progress_args=(status_message, start_time, "📥 DOWNLOADING")
            )

            if downloaded_path and os.path.exists(downloaded_path):
                download_time = time.time() - start_time
                actual_size = os.path.getsize(downloaded_path)
                speed = actual_size / download_time if download_time > 0 else 0
                
                logger.info(f"Download completed: {file_name} ({self.format_bytes(actual_size)}) in {download_time:.1f}s")
                
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
        
        # Only update every 5% progress or 2 seconds to reduce API calls
        if int(percent) % 5 != 0 and elapsed % 2 > 0.1:
            return

        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        # Create progress bar
        filled_blocks = int(percent / 5)
        bar = "█" * filled_blocks + "░" * (20 - filled_blocks)
        
        progress_text = (
            f"**{action}**\n\n"
            f"`{bar}`\n"
            f"**Progress:** {percent:.1f}%\n"
            f"**Speed:** {self.format_bytes(speed)}/s\n"
            f"**ETA:** {int(eta)}s | **Elapsed:** {int(elapsed)}s\n"
            f"`{self.format_bytes(current)} / {self.format_bytes(total)}`"
        )
        
        try:
            await status_message.edit_text(progress_text)
        except Exception as e:
            # Silent fail to avoid breaking download
            pass

    def format_bytes(self, size):
        """Format bytes to human readable"""
        if not size or size <= 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
            
        return f"{size:.1f} {units[unit_index]}"
