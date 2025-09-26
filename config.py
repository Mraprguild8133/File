import os

class Config:
    # API Configuration
    API_ID = int(os.getenv("API_ID", 123456))
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
    
    # Bot Settings
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", -100123456789))
    
    # Performance Optimization
    MAX_WORKERS = 50
    MAX_CONCURRENT_DOWNLOADS = 5
    MAX_CONCURRENT_UPLOADS = 5
    
    # Thumbnail Settings
    CUSTOM_THUMBNAIL = os.getenv("CUSTOM_THUMBNAIL", "thumbnail.jpg")
    THUMBNAIL_SIZE = (320, 320)
    
    # File Handling
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    CHUNK_SIZE = 64 * 1024  # 64KB chunks for faster processing
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = 30
    FILES_PER_USER_PER_HOUR = 10
