import os
from typing import List, Set

class Config:
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # Admin IDs (comma separated)
    ADMIN_IDS = set(int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(","))
    
    # Bot Settings
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    SUPPORTED_FORMATS = {
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',
        # Videos
        'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv',
        # Audio
        'mp3', 'wav', 'ogg', 'flac', 'm4a',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz'
    }
    
    # Thumbnail Settings
    THUMBNAIL_SIZE = (320, 320)
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = 10
    
    # Messages
    WELCOME_MESSAGE = """
🤖 **Welcome to PYRO RENAME BOT** 🚀

I can help you rename any file you send me! Here's what I can do:

📁 **Supported Files:**
- Documents (PDF, DOC, TXT, etc.)
- Images (JPG, PNG, GIF, etc.)
- Videos (MP4, AVI, MOV, etc.)
- Audio files (MP3, WAV, etc.)
- Archives (ZIP, RAR, etc.)

⚡ **How to use:**
1. Send me any file
2. Enter your desired filename
3. I'll send back the renamed file!

📊 **Features:**
- File size limit: 500MB
- Batch renaming support
- Custom thumbnail support
- Fast processing

Use /help to see all commands!
    """
    
    HELP_MESSAGE = """
🆘 **PYRO RENAME BOT - HELP**

**Commands:**
/start - Start the bot
/help - Show this help message
/about - About this bot
/status - Bot status
/batch - Enable batch renaming mode

**Admin Commands:**
/admin - Admin panel
/stats - Bot statistics
/broadcast - Broadcast message

**How to rename files:**
1. Send a file to the bot
2. Enter new filename when prompted
3. Receive renamed file

**Batch Renaming:**
1. Use /batch to enable batch mode
2. Send multiple files
3. Enter naming pattern
4. Receive all renamed files

**Need help?** Contact admin!
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
