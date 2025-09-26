import os
import logging
import tempfile
from PIL import Image, ImageOps
import asyncio
import aiofiles

logger = logging.getLogger(__name__)

async def download_file(file_obj, extension: str) -> str:
    """Download file to temporary location."""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{extension}')
        temp_path = temp_file.name
        temp_file.close()
        
        await file_obj.download_to_drive(temp_path)
        return temp_path
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None

def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_file_supported(extension: str) -> bool:
    """Check if file extension is supported."""
    from config import config
    return extension.lower() in config.SUPPORTED_FORMATS

def get_file_size(size_bytes: int) -> str:
    """Convert file size to human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def create_thumbnail(file_path: str, size: tuple) -> str:
    """Create thumbnail for image/video files."""
    try:
        with Image.open(file_path) as img:
            img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
            thumbnail_path = file_path + "_thumb.jpg"
            img.save(thumbnail_path, "JPEG", quality=85)
            return thumbnail_path
    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        return None

def cleanup_file(file_path: str):
    """Clean up temporary files."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")
