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
                # Validate thumbnail
                with Image.open(Config.CUSTOM_THUMBNAIL) as img:
                    img.thumbnail(Config.THUMBNAIL_SIZE)
                    logger.info(f"Custom thumbnail loaded: {Config.CUSTOM_THUMBNAIL}")
                return Config.CUSTOM_THUMBNAIL
        except Exception as e:
            logger.warning(f"Thumbnail load failed: {e}")
        
        # Create default thumbnail if needed
        return self.create_default_thumbnail()

    def create_default_thumbnail(self):
        """Create a default thumbnail"""
        try:
            img = Image.new('RGB', Config.THUMBNAIL_SIZE, color='#2563eb')
            img.save('default_thumb.jpg')
            logger.info("Default thumbnail created")
            return 'default_thumb.jpg'
        except Exception as e:
            logger.error(f"Failed to create default thumbnail: {e}")
            return None

    async def upload_file(self, client, chat_id, file_path, status_message, caption):
        """Upload file with turbo speed - CORRECTED SYNTAX"""
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

            # Upload with progress tracking - CORRECTED PARAMETERS
            await client.send_document(
                chat_id=chat_id,
                document=file_path,
                caption=caption,
                thumb=self.thumbnail,
                progress=self.progress_callback,
                progress_args=(status_message, start_time, "📤 UPLOADING")
            )

            upload_time = time.time() - start_time
            speed = file_size / upload_time if upload_time > 0 else 0
            
            logger.info(f"Upload completed: {file_name} in {upload_time:.1f}s")
            
            # Delete status message after successful upload
            try:
                await status_message.delete()
            except:
                pass
                
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
        
        # Only update every 5% progress or 2 seconds
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
        except Exception:
            # Silent fail to avoid breaking upload
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
