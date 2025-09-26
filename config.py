import os

class Config:
    # API Configuration
    API_ID = int(os.getenv("API_ID", ""))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Bot Settings
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1001234567890"))
    
    # Turbo Performance Settings
    MAX_WORKERS = 100  # Reduced for stability
    MAX_CONCURRENT_DOWNLOADS = 3  # Reduced for stability
    MAX_CONCURRENT_UPLOADS = 3    # Reduced for stability
    
    # Thumbnail Settings
    CUSTOM_THUMBNAIL = "thumbnail.jpg"
    THUMBNAIL_SIZE = (320, 320)
    
    # File Limits
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    USER_RATE_LIMIT = 20  # Files per hour per user
