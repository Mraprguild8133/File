import os

class Config:
    # API Configuration
    API_ID = int(os.getenv("API_ID", ""))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Bot Settings
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", ""))  # Required for logging
    
    # Performance Settings
    MAX_WORKERS = 100
    MAX_CONCURRENT_DOWNLOADS = 3
    MAX_CONCURRENT_UPLOADS = 3
    
    # Thumbnail Settings
    CUSTOM_THUMBNAIL = "https://envs.sh/5l9.jpg"
    THUMBNAIL_SIZE = (320, 320)
    
    # File Limits
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    USER_RATE_LIMIT = 20
    
    # Logging Settings
    LOG_UPLOADS = True
    LOG_DOWNLOADS = True
