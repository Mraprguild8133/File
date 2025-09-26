import os
from typing import Set

class Config:
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # API ID and HASH from https://my.telegram.org
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    
    # Admin IDs (comma separated)
    ADMIN_IDS = set(int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(","))
    
    # Bot Settings
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    CHUNK_SIZE = 1 * 1024 * 1024  # 1MB chunks for upload
    DOWNLOAD_PATH = "downloads"
    UPLOAD_PATH = "uploads"
    
    # Supported formats (extended for 4GB files)
    SUPPORTED_FORMATS = {
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx',
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff',
        # Videos
        'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'm4v', '3gp',
        # Audio
        'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'wma',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz', 'bz2',
        # Executables
        'exe', 'msi', 'apk', 'deb', 'rpm',
        # Other
        'iso', 'dmg', 'csv', 'json', 'xml'
    }
    
    # Thumbnail Settings
    THUMBNAIL_SIZE = (320, 320)
    
    # Progress update intervals (in bytes)
    PROGRESS_UPDATE_INTERVAL = 50 * 1024 * 1024  # 50MB
    
    # Messages
    WELCOME_MESSAGE = """
🤖 **PYRO RENAME BOT v3.0** 🚀

**Now with 4GB File Support!** 📁

I can rename files up to **4GB** in size! Here's what I can do:

📁 **Supported Files (Up to 4GB):**
- Documents (PDF, DOC, XLS, PPT, etc.)
- Images (JPG, PNG, GIF, etc.)
- Videos (MP4, AVI, MKV, etc.)
- Audio files (MP3, WAV, FLAC, etc.)
- Archives (ZIP, RAR, 7Z, etc.)
- And many more!

⚡ **How to use:**
1. Send me any file (up to 4GB)
2. Enter your desired filename
3. I'll send back the renamed file with progress updates!

🔧 **Advanced Features:**
- Real-time upload/download progress
- Batch renaming support
- Custom thumbnail generation
- Fast streaming for large files

Use /help to see all commands!
    """
    
    HELP_MESSAGE = """
🆘 **PYRO RENAME BOT - HELP**

**⚡ Commands:**
/start - Start the bot
/help - Show this help message
/about - About this bot
/status - Bot status
/batch - Enable batch renaming mode

**👨‍💻 Admin Commands:**
/admin - Admin panel
/stats - Bot statistics
/broadcast - Broadcast message

**📁 How to rename files:**
1. Send a file to the bot (up to 4GB)
2. Enter new filename when prompted
3. Watch real-time progress
4. Receive renamed file

**🔄 Batch Renaming:**
1. Use /batch to enable batch mode
2. Send multiple files
3. Enter naming pattern
4. Receive all renamed files

**⚡ Need help?** Contact admin!
    """

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "INFO"

# Set configuration based on environment
if os.getenv("ENVIRONMENT") == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()
