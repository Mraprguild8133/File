import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class TurboUploader:
    """Turbo-optimized file uploader with thumbnail support"""
    
    def __init__(self):
        self.thumbnail = self.load_thumbnail()

    def load_thumbnail(self):
        """Load or create thumbnail"""
        try:
            if os.path.exists(Config.CUSTOM_THUMBNAIL):
                with Image.open(Config.CUSTOM_THUMBNAIL) as img:
                    img.thumbnail(Config.THUMBNAIL_SIZE)
                return Config.CUSTOM_THUMBNAIL
        except Exception as e:
            logger.warning(f"Thumbnail load failed: {e}")
        return None

    async def upload_file(self, client, chat_id, file_path, status_message, caption):
        """Upload file with turbo speed"""
        start_time = time.time()
        
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}

            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            await status_message.edit_text(
                f"📤 **Turbo Upload Starting...**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {self.format_bytes(file_size)}"
            )

            # Upload with turbo settings
            await client.send_document(
                chat_id=chat_id,
                document=file_path,
                caption=caption,
                thumb=self.thumbnail,
                progress=self.progress_callback,
                progress_args=(status_message, start_time, "📤 UPLOADING"),
                chunk_size=Config.CHUNK_SIZE,
                disable_notification=True
            )

            upload_time = time.time() - start_time
            speed = file_size / upload_time if upload_time > 0 else 0
            
            logger.info(f"Upload completed: {file_name} in {upload_time:.1f}s")
            
            return {'success': True, 'upload_time': upload_time, 'speed': speed}

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {'success': False, 'error': str(e)}

    async def progress_callback(self, current, total, status_message, start_time, action):
        """Upload progress callback"""
        if total == 0:
            return

        elapsed = time.time() - start_time
        percent = (current / total) * 100
        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        # Update every 5% or 3 seconds
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
