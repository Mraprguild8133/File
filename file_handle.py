import time
import asyncio
import aiofiles
import os
from pathlib import Path
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError
from config import Config
from PIL import Image, ImageDraw, ImageFont
import logging
from concurrent.futures import ThreadPoolExecutor
import shutil

# Configure logging
logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive operations
thread_pool = ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_DOWNLOADS)

class TurboFileHandler:
    """
    Turbo-optimized file handler with custom thumbnail support and extreme speed.
    """
    def __init__(self):
        self.download_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_DOWNLOADS)
        self.upload_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_UPLOADS)
        self.thumbnail_path = self._load_or_create_thumbnail()
        self.progress_cache = {}  # Cache progress updates to reduce API calls

    def _load_or_create_thumbnail(self):
        """Load existing thumbnail or create a default one."""
        thumbnail_path = Config.CUSTOM_THUMBNAIL
        
        # Check if custom thumbnail exists
        if os.path.exists(thumbnail_path):
            try:
                # Validate and optimize thumbnail
                with Image.open(thumbnail_path) as img:
                    img.thumbnail(Config.THUMBNAIL_SIZE)
                    logger.info(f"Custom thumbnail loaded: {thumbnail_path}")
                return thumbnail_path
            except Exception as e:
                logger.warning(f"Failed to load custom thumbnail: {e}")
        
        # Create default thumbnail
        return self._create_default_thumbnail()

    def _create_default_thumbnail(self):
        """Create a default thumbnail for the bot."""
        try:
            # Create a modern-looking thumbnail
            img = Image.new('RGB', Config.THUMBNAIL_SIZE, color='#2563eb')
            draw = ImageDraw.Draw(img)
            
            # Try to use a nice font, fallback to default
            try:
                font_large = ImageFont.truetype("arialbd.ttf", 32)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                try:
                    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                except:
                    font_large = ImageFont.load_default()
                    font_small = ImageFont.load_default()

            # Draw main text
            text = "TURBO BOT"
            bbox = draw.textbbox((0, 0), text, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (Config.THUMBNAIL_SIZE[0] - text_width) // 2
            y = (Config.THUMBNAIL_SIZE[1] - text_height) // 2 - 20
            
            draw.text((x, y), text, font=font_large, fill='white')
            
            # Draw subtitle
            subtitle = "File Renamer"
            bbox_sub = draw.textbbox((0, 0), subtitle, font=font_small)
            sub_width = bbox_sub[2] - bbox_sub[0]
            x_sub = (Config.THUMBNAIL_SIZE[0] - sub_width) // 2
            draw.text((x_sub, y + text_height + 10), subtitle, font=font_small, fill='#d1d5db')
            
            # Save thumbnail
            img.save("default_thumbnail.jpg", "JPEG", quality=95)
            logger.info("Default thumbnail created successfully")
            return "default_thumbnail.jpg"
            
        except Exception as e:
            logger.error(f"Failed to create default thumbnail: {e}")
            return None

    async def optimize_thumbnail(self, thumbnail_path):
        """Optimize thumbnail for faster uploads."""
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            return None
            
        try:
            optimized_path = f"optimized_{os.path.basename(thumbnail_path)}"
            
            # Run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                thread_pool, 
                self._optimize_thumbnail_sync, 
                thumbnail_path, 
                optimized_path
            )
            
            return optimized_path if os.path.exists(optimized_path) else thumbnail_path
        except Exception as e:
            logger.warning(f"Thumbnail optimization failed: {e}")
            return thumbnail_path

    def _optimize_thumbnail_sync(self, input_path, output_path):
        """Synchronous thumbnail optimization."""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Optimize size and quality
                img.thumbnail(Config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                img.save(output_path, "JPEG", optimize=True, quality=85)
        except Exception as e:
            logger.error(f"Thumbnail optimization error: {e}")
            shutil.copy2(input_path, output_path)

async def download_file_turbo(message: Message, status_message: Message):
    """
    Turbo-optimized file download with progress tracking and error handling.
    
    Args:
        message: The message containing the file
        status_message: Message to update with progress
        
    Returns:
        str: Path to downloaded file or None if failed
    """
    handler = TurboFileHandler()
    start_time = time.time()
    download_id = f"{message.chat.id}_{message.id}"
    
    async with handler.download_semaphore:
        try:
            file_to_download = message.document or message.video or message.audio
            if not file_to_download:
                await status_message.edit_text("❌ **No downloadable file found**")
                return None

            # Validate file size
            file_size = getattr(file_to_download, 'file_size', 0)
            if file_size > Config.MAX_FILE_SIZE:
                await status_message.edit_text(
                    f"❌ **File too large!**\n\n"
                    f"Maximum size: {_format_bytes(Config.MAX_FILE_SIZE)}\n"
                    f"Your file: {_format_bytes(file_size)}"
                )
                return None

            # Get file name
            file_name = getattr(file_to_download, 'file_name', 'file')
            await status_message.edit_text(
                f"📥 **Starting Download**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {_format_bytes(file_size)}\n"
                f"**Status:** Preparing..."
            )

            # Create downloads directory
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)

            # Download with turbo optimization
            file_path = await message.download(
                file_name=str(download_dir / file_name),
                progress=_turbo_progress_callback,
                progress_args=(status_message, start_time, "📥 DOWNLOADING", download_id, handler),
                chunk_size=Config.CHUNK_SIZE * 4,  # Larger chunks for speed
                max_connections=4  # Multiple connections for large files
            )

            if file_path and os.path.exists(file_path):
                actual_size = os.path.getsize(file_path)
                download_time = time.time() - start_time
                speed = actual_size / download_time if download_time > 0 else 0
                
                logger.info(
                    f"Download completed: {file_name} "
                    f"({_format_bytes(actual_size)}) in {download_time:.1f}s "
                    f"({_format_bytes(speed)}/s)"
                )
                
                return file_path
            else:
                await status_message.edit_text("❌ **Download failed - file not saved**")
                return None

        except FloodWait as e:
            wait_time = e.value
            await status_message.edit_text(
                f"⏳ **Rate limit reached**\n\n"
                f"Please wait {wait_time} seconds before trying again."
            )
            await asyncio.sleep(wait_time)
            return None
            
        except RPCError as e:
            await status_message.edit_text(f"❌ **Telegram error:** {str(e)}")
            return None
            
        except Exception as e:
            await status_message.edit_text(f"❌ **Download error:** {str(e)}")
            logger.error(f"Download failed: {e}")
            return None

async def upload_file_turbo(client, chat_id, file_path, status_message: Message, caption=""):
    """
    Turbo-optimized file upload with custom thumbnail and progress tracking.
    
    Args:
        client: Pyrogram client
        chat_id: Target chat ID
        file_path: Path to file to upload
        status_message: Message to update with progress
        caption: File caption
    """
    if not os.path.exists(file_path):
        await status_message.edit_text("❌ **File not found for upload**")
        return

    handler = TurboFileHandler()
    start_time = time.time()
    upload_id = f"{chat_id}_{os.path.basename(file_path)}"
    
    async with handler.upload_semaphore:
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            await status_message.edit_text(
                f"📤 **Starting Upload**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {_format_bytes(file_size)}\n"
                f"**Status:** Preparing..."
            )

            # Optimize thumbnail
            thumb = await handler.optimize_thumbnail(handler.thumbnail_path)
            
            # Upload parameters for maximum speed
            upload_kwargs = {
                'chat_id': chat_id,
                'document': file_path,
                'caption': caption,
                'thumb': thumb,
                'progress': _turbo_progress_callback,
                'progress_args': (status_message, start_time, "📤 UPLOADING", upload_id, handler),
                'chunk_size': Config.CHUNK_SIZE * 4,
                'disable_notification': True,  # Faster without notifications
                'force_document': True,  # Always as document for consistency
            }

            # Perform upload
            await client.send_document(**upload_kwargs)
            
            upload_time = time.time() - start_time
            speed = file_size / upload_time if upload_time > 0 else 0
            
            logger.info(
                f"Upload completed: {file_name} "
                f"({_format_bytes(file_size)}) in {upload_time:.1f}s "
                f"({_format_bytes(speed)}/s)"
            )
            
            # Delete status message after successful upload
            try:
                await status_message.delete()
            except:
                pass  # Silent fail if message already deleted

        except FloodWait as e:
            wait_time = e.value
            await status_message.edit_text(
                f"⏳ **Upload rate limit**\n\n"
                f"Please wait {wait_time} seconds before trying again."
            )
            await asyncio.sleep(wait_time)
            
        except RPCError as e:
            await status_message.edit_text(f"❌ **Upload error:** {str(e)}")
            
        except Exception as e:
            await status_message.edit_text(f"❌ **Upload failed:** {str(e)}")
            logger.error(f"Upload failed: {e}")

async def _turbo_progress_callback(current, total, status_message: Message, start_time, action, operation_id, handler):
    """
    Ultra-optimized progress callback with minimal API calls and caching.
    """
    if total == 0:
        return

    current_time = time.time()
    elapsed = current_time - start_time
    
    # Cache progress to avoid too many API calls
    cache_key = f"{operation_id}_{int(current/total*100)}"
    if cache_key in handler.progress_cache:
        if current_time - handler.progress_cache[cache_key] < 2.0:  # 2-second cache
            return
    
    handler.progress_cache[cache_key] = current_time
    
    # Clean old cache entries
    current_cache = handler.progress_cache.copy()
    for key, timestamp in current_cache.items():
        if current_time - timestamp > 30:  # 30-second cache lifetime
            handler.progress_cache.pop(key, None)

    percentage = (current / total) * 100
    speed = current / elapsed if elapsed > 0 else 0
    eta = (total - current) / speed if speed > 0 else 0
    
    # Create progress bar
    filled_length = int(30 * percentage // 100)
    bar = '█' * filled_length + '░' * (30 - filled_length)
    
    # Format progress text
    progress_text = (
        f"**{action}**\n\n"
        f"`{bar}`\n"
        f"**Progress:** {percentage:.1f}%\n"
        f"**Speed:** {_format_bytes(speed)}/s\n"
        f"**ETA:** {_format_time(eta)} | **Elapsed:** {_format_time(elapsed)}\n"
        f"`{_format_bytes(current)} / {_format_bytes(total)}`"
    )
    
    try:
        # Only update if text has changed significantly
        if (not hasattr(status_message, 'last_progress_text') or 
            status_message.last_progress_text != progress_text):
            await status_message.edit_text(progress_text)
            status_message.last_progress_text = progress_text
    except Exception as e:
        # Silent fail to avoid breaking the upload/download
        pass

def _format_bytes(size):
    """Ultra-fast bytes formatting."""
    if not size or size <= 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
        
    return f"{size:.2f} {units[unit_index]}"

def _format_time(seconds):
    """Format time in a human-readable way."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

async def cleanup_files(*file_paths):
    """
    Clean up temporary files efficiently.
    
    Args:
        *file_paths: Variable number of file paths to delete
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                # Use thread pool for file operations
                await asyncio.get_event_loop().run_in_executor(
                    thread_pool, os.remove, file_path
                )
                logger.debug(f"Cleaned up file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")

async def get_file_info(file_path):
    """
    Get detailed information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        dict: File information
    """
    if not os.path.exists(file_path):
        return None
        
    try:
        stat = await asyncio.get_event_loop().run_in_executor(
            thread_pool, os.stat, file_path
        )
        
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1].lower()
        }
    except Exception as e:
        logger.error(f"Failed to get file info: {e}")
        return None

# Backward compatibility functions
async def download_file(message: Message, status_message: Message):
    """Legacy download function for compatibility."""
    return await download_file_turbo(message, status_message)

async def upload_file(client, chat_id, file_path, status_message: Message, caption=""):
    """Legacy upload function for compatibility."""
    return await upload_file_turbo(client, chat_id, file_path, status_message, caption)

# Initialize global handler instance
turbo_handler = TurboFileHandler()
