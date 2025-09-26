import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
import logging

logger = logging.getLogger(__name__)

class TurboDownloader:
    """Turbo-optimized file downloader with flood protection"""
    
    def __init__(self):
        self.last_update_time = 0
        self.last_percent = 0

    async def download_file(self, message: Message, status_message: Message):
        """Download file with flood protection"""
        start_time = time.time()
        self.last_update_time = 0
        self.last_percent = 0
        
        try:
            file_obj = message.document or message.video or message.audio
            if not file_obj:
                return {'success': False, 'error': 'No file found'}

            file_name = getattr(file_obj, 'file_name', 'file')
            file_size = getattr(file_obj, 'file_size', 0)

            # Create downloads directory
            os.makedirs('downloads', exist_ok=True)
            file_path = os.path.join('downloads', f"temp_{int(time.time())}_{file_name}")

            # Initial status message (only once)
            initial_text = (
                f"📥 **Downloading...**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {self.format_bytes(file_size)}\n"
                f"**Status:** Starting..."
            )
            await status_message.edit_text(initial_text)

            # Download with progress tracking
            downloaded_path = await message.download(
                file_name=file_path,
                progress=self.progress_callback,
                progress_args=(status_message, start_time, "📥 DOWNLOADING")
            )

            if downloaded_path and os.path.exists(downloaded_path):
                download_time = time.time() - start_time
                actual_size = os.path.getsize(downloaded_path)
                speed = actual_size / download_time if download_time > 0 else 0
                
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
        """Flood-protected progress callback"""
        if total == 0:
            return

        current_time = time.time()
        elapsed = current_time - start_time
        percent = (current / total) * 100
        
        # Flood protection: Update only if:
        # 1. At least 3 seconds passed since last update AND progress increased by at least 2%
        # 2. Or if it's the first update
        # 3. Or if download is complete (100%)
        should_update = (
            current_time - self.last_update_time >= 3 and 
            percent - self.last_percent >= 2
        ) or self.last_update_time == 0 or percent >= 99.9

        if not should_update:
            return

        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        # Create progress bar (only 10 blocks for fewer updates)
        filled_blocks = min(10, int(percent / 10))
        bar = "▓" * filled_blocks + "░" * (10 - filled_blocks)
        
        progress_text = (
            f"**{action}**\n\n"
            f"`{bar} {percent:.1f}%`\n"
            f"**Speed:** {self.format_bytes(speed)}/s\n"
            f"**Time:** {int(elapsed)}s / ~{int(eta)}s\n"
            f"**Progress:** {self.format_bytes(current)} / {self.format_bytes(total)}"
        )
        
        try:
            await status_message.edit_text(progress_text)
            self.last_update_time = current_time
            self.last_percent = percent
        except Exception as e:
            # If flood wait error, wait and retry
            if "FLOOD_WAIT" in str(e):
                wait_time = int(str(e).split("FLOOD_WAIT_")[1].split(")")[0])
                logger.warning(f"Flood wait detected, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            # For other errors, just skip this update
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
