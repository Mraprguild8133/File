import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class TurboUploader:
    """Turbo-optimized file uploader with duplicate prevention"""
    
    def __init__(self):
        self.thumbnail = self.load_thumbnail()
        self.last_update_time = 0
        self.last_percent = 0
        self.last_message_text = ""

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
        """Upload file with duplicate prevention"""
        start_time = time.time()
        self.last_update_time = 0
        self.last_percent = 0
        self.last_message_text = ""
        
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}

            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            # Initial status (only once)
            initial_text = (
                f"📤 **Uploading File**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {self.format_bytes(file_size)}\n"
                f"**Status:** Starting upload..."
            )
            await status_message.edit_text(initial_text)
            self.last_message_text = initial_text

            # Upload with progress tracking
            await client.send_document(
                chat_id=chat_id,
                document=file_path,
                caption=caption,
                thumb=self.thumbnail,
                progress=self.progress_callback,
                progress_args=(status_message, start_time, "UPLOADING")
            )

            upload_time = time.time() - start_time
            speed = file_size / upload_time if upload_time > 0 else 0
            
            logger.info(f"Upload completed: {file_name} in {upload_time:.1f}s")
            
            # Final completion message (only if different)
            completion_text = (
                f"✅ **Upload Complete**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Time:** {int(upload_time)} seconds\n"
                f"**Speed:** {self.format_bytes(speed)}/s"
            )
            
            if completion_text != self.last_message_text:
                await status_message.edit_text(completion_text)
                await asyncio.sleep(2)
                await status_message.delete()
                
            return {'success': True, 'upload_time': upload_time, 'speed': speed}

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {'success': False, 'error': str(e)}

    async def progress_callback(self, current, total, status_message, start_time, action):
        """Duplicate-protected upload progress callback"""
        if total == 0:
            return

        current_time = time.time()
        elapsed = current_time - start_time
        percent = (current / total) * 100
        
        # Prevent duplicates: Update only if:
        # 1. At least 6 seconds passed since last update
        # 2. AND progress increased by at least 8%
        # 3. OR it's the first update
        # 4. OR upload is complete (95%+)
        time_passed = current_time - self.last_update_time
        progress_increased = percent - self.last_percent
        
        should_update = (
            (time_passed >= 6 and progress_increased >= 8) or
            self.last_update_time == 0 or
            percent >= 95
        )

        if not should_update:
            return

        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        progress_text = (
            f"📤 **Uploading File**\n\n"
            f"**Progress:** {percent:.1f}%\n"
            f"**Speed:** {self.format_bytes(speed)}/s\n"
            f"**Remaining:** ~{int(eta)} seconds\n"
            f"**Transferred:** {self.format_bytes(current)} / {self.format_bytes(total)}"
        )
        
        # Only update if message content actually changed
        if progress_text != self.last_message_text:
            try:
                await status_message.edit_text(progress_text)
                self.last_message_text = progress_text
                self.last_update_time = current_time
                self.last_percent = percent
            except Exception as e:
                if "FLOOD_WAIT" in str(e):
                    try:
                        wait_time = int(str(e).split("FLOOD_WAIT_")[1].split(")")[0])
                        logger.info(f"Upload flood wait: {wait_time}s")
                        await asyncio.sleep(wait_time)
                    except:
                        pass
                # Skip update for other errors

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
