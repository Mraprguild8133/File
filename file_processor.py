import os
import time
import asyncio
from pyrogram.types import Message
from config import Config
from turbo_uploader import TurboUploader
from turbo_downloader import TurboDownloader
import logging

logger = logging.getLogger(__name__)

class TurboFileProcessor:
    """Main file processor with turbo speed"""
    
    def __init__(self):
        self.downloader = TurboDownloader()
        self.uploader = TurboUploader()
        self.processing_tasks = {}

    async def process_file(self, client, file_message, new_filename, status_message, chat_id):
        """Process file with turbo speed"""
        try:
            # Step 1: Download file
            download_result = await self.downloader.download_file(
                file_message, status_message
            )
            
            if not download_result['success']:
                return download_result

            # Step 2: Rename file
            rename_result = await self.rename_file(
                download_result['file_path'], new_filename
            )
            
            if not rename_result['success']:
                await self.cleanup_files(download_result['file_path'])
                return rename_result

            # Step 3: Upload file
            upload_result = await self.uploader.upload_file(
                client, chat_id, rename_result['file_path'], status_message,
                f"**Renamed to:** `{os.path.basename(rename_result['file_path'])}`"
            )

            # Step 4: Cleanup
            await self.cleanup_files(
                download_result['file_path'], 
                rename_result['file_path']
            )

            return upload_result

        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {'success': False, 'error': str(e)}

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
                except Exception as e:
                    logger.warning(f"Cleanup failed for {file_path}: {e}")
