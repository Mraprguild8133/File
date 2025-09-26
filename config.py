import os

class Config:
    # API Configuration
    API_ID = int(os.getenv("API_ID", "1234567"))  # Replace with your API ID
    API_HASH = os.getenv("API_HASH", "your_api_hash_here")  # Replace with your API HASH
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")  # Replace with your BOT TOKEN
    
    # Bot Settings
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1001234567890"))  # Optional: Your channel ID
    
    # Performance Settings
    MAX_WORKERS = 100
    MAX_CONCURRENT_TRANSMISSIONS = 10
    
    # File Settings
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    
    # Thumbnail Settings
    CUSTOM_THUMBNAIL = "thumbnail.jpg"  # Optional custom thumbnail

# Validate required configuration
required_vars = ["API_ID", "API_HASH", "BOT_TOKEN"]
for var in required_vars:
    if not getattr(Config, var):
        raise ValueError(f"Missing required configuration: {var}")
