import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
from turbo_uploader import TurboUploader
from turbo_downloader import TurboDownloader
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TurboFileProcessor:
    """Main file processor with complete logging"""
    
    def __init__(self):
        self.downloader = TurboDownloader()
        self.uploader = TurboUploader()

    async def process_file(self, client, file_message, new_filename, status_message, chat_id):
        """Process file with complete logging"""
        downloaded_path = None
        renamed_path = None
        original_file_info = None
        
        try:
            # Get original file info for logging
            original_file_info = await self.get_file_info(file_message)
            
            # Step 1: Download file
            download_result = await self.downloader.download_file(file_message, status_message)
            
            if not download_result['success']:
                await self.log_activity(client, "DOWNLOAD_FAILED", original_file_info, download_result['error'])
                return download_result

            downloaded_path = download_result['file_path']

            # Step 2: Rename file
            rename_result = await self.rename_file(downloaded_path, new_filename)
            
            if not rename_result['success']:
                await self.cleanup_files(downloaded_path)
                await self.log_activity(client, "RENAME_FAILED", original_file_info, rename_result['error'])
                return rename_result

            renamed_path = rename_result['file_path']

            # Step 3: Upload file
            caption = f"**Renamed to:** `{os.path.basename(renamed_path)}`"
            upload_result = await self.uploader.upload_file(
                client, chat_id, renamed_path, status_message, caption
            )

            # Step 4: Log activity
            if upload_result['success']:
                await self.log_success(client, original_file_info, upload_result, new_filename)
            else:
                await self.log_activity(client, "UPLOAD_FAILED", original_file_info, upload_result['error'])

            return upload_result

        except Exception as e:
            logger.error(f"Processing error: {e}")
            await self.log_activity(client, "PROCESSING_ERROR", original_file_info, str(e))
            return {'success': False, 'error': str(e)}
        finally:
            # Always cleanup temporary files
            await self.cleanup_files(downloaded_path, renamed_path)

    async def get_file_info(self, message):
        """Extract file information for logging"""
        file_obj = message.document or message.video or message.audio
        if not file_obj:
            return None
            
        return {
            'file_name': getattr(file_obj, 'file_name', 'Unknown'),
            'file_size': getattr(file_obj, 'file_size', 0),
            'mime_type': getattr(file_obj, 'mime_type', 'Unknown'),
            'user_id': message.from_user.id if message.from_user else None,
            'username': message.from_user.username if message.from_user else None,
            'message_id': message.id,
            'chat_id': message.chat.id
        }

    async def log_success(self, client, file_info, upload_result, new_filename):
        """Log successful file processing"""
        if not Config.LOG_CHANNEL:
            return
            
        try:
            user_info = f"@{file_info['username']}" if file_info['username'] else f"User ID: {file_info['user_id']}"
            
            log_message = (
                f"✅ **File Processing Successful**\n\n"
                f"**User:** {user_info}\n"
                f"**Original File:** `{file_info['file_name']}`\n"
                f"**Renamed To:** `{new_filename}`\n"
                f"**File Size:** {self.format_bytes(file_info['file_size'])}\n"
                f"**Upload Time:** {upload_result['upload_time']:.1f}s\n"
                f"**Upload Speed:** {self.format_bytes(upload_result['speed'])}/s\n"
                f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await client.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=log_message
            )
            
            # Also forward the original message if possible
            try:
                await client.forward_messages(
                    chat_id=Config.LOG_CHANNEL,
                    from_chat_id=file_info['chat_id'],
                    message_ids=file_info['message_id']
                )
            except Exception as e:
                logger.warning(f"Could not forward message to log channel: {e}")
                
        except Exception as e:
            logger.error(f"Failed to log success: {e}")

    async def log_activity(self, client, activity_type, file_info, error_message=None):
        """Log various activities"""
        if not Config.LOG_CHANNEL:
            return
            
        try:
            user_info = f"@{file_info['username']}" if file_info and file_info['username'] else f"User ID: {file_info['user_id']}" if file_info else "Unknown User"
            file_name = file_info['file_name'] if file_info else "Unknown File"
            
            if activity_type == "DOWNLOAD_FAILED":
                log_text = f"❌ **Download Failed**\n\nUser: {user_info}\nFile: `{file_name}`\nError: {error_message}"
            elif activity_type == "UPLOAD_FAILED":
                log_text = f"❌ **Upload Failed**\n\nUser: {user_info}\nFile: `{file_name}`\nError: {error_message}"
            elif activity_type == "RENAME_FAILED":
                log_text = f"❌ **Rename Failed**\n\nUser: {user_info}\nFile: `{file_name}`\nError: {error_message}"
            else:
                log_text = f"⚠️ **Processing Error**\n\nUser: {user_info}\nError: {error_message}"
            
            log_text += f"\n**Time:** {datetime.now().strftime('%H:%M:%S')}"
            
            await client.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=log_text
            )
            
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    async def rename_file(self, file_path, new_name):
        """Rename file with extension preservation"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}

            # Get file extension
            dir_name = os.path.dirname(file_path)
            file_ext = os.path.splitext(file_path)[1]
            
            # Create new path
            new_path = os.path.join(dir_name, f"{new_name}{file_ext}")
            
            # Rename file
            os.rename(file_path, new_path)
            
            return {'success': True, 'file_path': new_path}
            
        except Exception as e:
            return {'success': False, 'error': f'Rename failed: {str(e)}'}

    async def cleanup_files(self, *file_paths):
        """Cleanup temporary files"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up: {file_path}")
                except Exception as e:
                    logger.warning(f"Cleanup failed for {file_path}: {e}")

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
