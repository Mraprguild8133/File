import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class TurboUploader:
    """Turbo-optimized file uploader with flood protection"""
    
    def __init__(self):
        self.thumbnail = self.load_thumbnail()
        self.last_update_time = 0
        self.last_percent = 0

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
        """Upload file with flood protection"""
        start_time = time.time()
        self.last_update_time = 0
        self.last_percent = 0
        
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}

            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            # Initial status (only once)
            initial_text = (
                f"📤 **Uploading...**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {self.format_bytes(file_size)}\n"
                f"**Status:** Starting..."
            )
            await status_message.edit_text(initial_text)

            # Upload with progress tracking
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
            
            # Final completion message
            completion_text = (
                f"✅ **Upload Complete!**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Time:** {int(upload_time)}s\n"
                f"**Speed:** {self.format_bytes(speed)}/s"
            )
            
            try:
                await status_message.edit_text(completion_text)
                # Delete after 3 seconds
                await asyncio.sleep(3)
                await status_message.delete()
            except:
                pass
                
            return {'success': True, 'upload_time': upload_time, 'speed': speed}

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {'success': False, 'error': str(e)}

    async def progress_callback(self, current, total, status_message, start_time, action):
        """Flood-protected upload progress callback"""
        if total == 0:
            return

        current_time = time.time()
        elapsed = current_time - start_time
        percent = (current / total) * 100
        
        # Flood protection: Update only if:
        # 1. At least 4 seconds passed AND progress increased by at least 3%
        # 2. Or if it's the first update
        # 3. Or if upload is complete
        should_update = (
            current_time - self.last_update_time >= 4 and 
            percent - self.last_percent >= 3
        ) or self.last_update_time == 0 or percent >= 99.9

        if not should_update:
            return

        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        # Simple progress display
        filled_blocks = min(8, int(percent / 12.5))
        bar = "█" * filled_blocks + "▒" * (8 - filled_blocks)
        
        progress_text = (
            f"**{action}**\n\n"
            f"`{bar} {percent:.1f}%`\n"
            f"**Speed:** {self.format_bytes(speed)}/s\n"
            f"**Remaining:** ~{int(eta)}s\n"
            f"**Progress:** {self.format_bytes(current)} / {self.format_bytes(total)}"
        )
        
        try:
            await status_message.edit_text(progress_text)
            self.last_update_time = current_time
            self.last_percent = percent
        except Exception as e:
            # Handle flood wait specifically
            if "FLOOD_WAIT" in str(e):
                wait_time = int(str(e).split("FLOOD_WAIT_")[1].split(")")[0])
                logger.warning(f"Upload flood wait: {wait_time}s")
                await asyncio.sleep(wait_time)
            # Skip update for other errors
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
