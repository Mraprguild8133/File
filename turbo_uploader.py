import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

class TurboUploader:
    """Turbo-optimized file uploader with advanced thumbnail support"""
    
    def __init__(self):
        self.thumbnail = self.create_or_load_thumbnail()
        self.last_update_time = 0
        self.last_percent = 0
        self.last_message_text = ""

    def create_or_load_thumbnail(self):
        """Create or load thumbnail with advanced features"""
        try:
            # Try to load custom thumbnail
            if os.path.exists(Config.CUSTOM_THUMBNAIL):
                with Image.open(Config.CUSTOM_THUMBNAIL) as img:
                    img = self.process_thumbnail(img)
                    thumb_path = "processed_thumbnail.jpg"
                    img.save(thumb_path, "JPEG", quality=95)
                    logger.info("Custom thumbnail loaded and processed")
                    return thumb_path
        except Exception as e:
            logger.warning(f"Custom thumbnail failed: {e}")

        # Create default thumbnail
        return self.create_default_thumbnail()

    def process_thumbnail(self, img):
        """Process thumbnail for optimal quality"""
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to optimal dimensions
        img.thumbnail(Config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        return img

    def create_default_thumbnail(self):
        """Create a beautiful default thumbnail"""
        try:
            # Create image with gradient background
            img = Image.new('RGB', Config.THUMBNAIL_SIZE, color='#2563eb')
            draw = ImageDraw.Draw(img)
            
            # Add gradient effect
            for i in range(Config.THUMBNAIL_SIZE[1]):
                ratio = i / Config.THUMBNAIL_SIZE[1]
                color = self.interpolate_color('#2563eb', '#1e40af', ratio)
                draw.line([(0, i), (Config.THUMBNAIL_SIZE[0], i)], fill=color)
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("arialbd.ttf", 36)
                subtitle_font = ImageFont.truetype("arial.ttf", 18)
            except:
                # Fallback to default fonts
                try:
                    title_font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
                except:
                    title_font = None
                    subtitle_font = None

            # Add main text
            text = "TURBO BOT"
            if title_font:
                bbox = draw.textbbox((0, 0), text, font=title_font)
                text_width = bbox[2] - bbox[0]
                x = (Config.THUMBNAIL_SIZE[0] - text_width) // 2
                y = Config.THUMBNAIL_SIZE[1] // 2 - 30
                draw.text((x, y), text, font=title_font, fill='white')
            
            # Add subtitle
            subtitle = "File Renamer"
            if subtitle_font:
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                sub_width = bbox[2] - bbox[0]
                x_sub = (Config.THUMBNAIL_SIZE[0] - sub_width) // 2
                y_sub = y + 50
                draw.text((x_sub, y_sub), subtitle, font=subtitle_font, fill='#e5e7eb')
            
            # Save thumbnail
            thumb_path = "default_thumbnail.jpg"
            img.save(thumb_path, "JPEG", quality=90, optimize=True)
            logger.info("Default thumbnail created successfully")
            return thumb_path
            
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            return None

    def interpolate_color(self, color1, color2, ratio):
        """Create gradient color"""
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f'#{r:02x}{g:02x}{b:02x}'

    async def upload_file(self, client, chat_id, file_path, status_message, caption):
        """Upload file with thumbnail and logging"""
        start_time = time.time()
        self.last_update_time = 0
        self.last_percent = 0
        self.last_message_text = ""
        
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}

            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            # Initial status
            initial_text = (
                f"📤 **Uploading File**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {self.format_bytes(file_size)}\n"
                f"**Thumbnail:** {'✅' if self.thumbnail else '❌'}\n"
                f"**Status:** Starting upload..."
            )
            await status_message.edit_text(initial_text)
            self.last_message_text = initial_text

            # Upload with thumbnail
            message = await client.send_document(
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
            
            # Return message object for logging
            return {
                'success': True, 
                'upload_time': upload_time, 
                'speed': speed,
                'message': message,
                'file_name': file_name,
                'file_size': file_size
            }

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {'success': False, 'error': str(e)}

    async def progress_callback(self, current, total, status_message, start_time, action):
        """Progress callback with thumbnail status"""
        if total == 0:
            return

        current_time = time.time()
        elapsed = current_time - start_time
        percent = (current / total) * 100
        
        # Update conditions
        time_passed = current_time - self.last_update_time
        progress_increased = percent - self.last_percent
        
        should_update = (
            (time_passed >= 5 and progress_increased >= 5) or
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
            f"**Thumbnail:** {'✅' if self.thumbnail else '❌'}\n"
            f"**ETA:** ~{int(eta)}s\n"
            f"**Transferred:** {self.format_bytes(current)} / {self.format_bytes(total)}"
        )
        
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
                        await asyncio.sleep(wait_time)
                    except:
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
