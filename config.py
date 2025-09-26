# =====================================================================================
# Project: Telegram File Rename Bot - Configuration File
# Description: All settings and API keys for the bot are stored here.
# Last Updated: 26-Sep-2025
# =====================================================================================

import os

class Config(object):
    """
    Bot configuration variables.
    You MUST fill in the values for the bot to work.
    """
    
    # Get these values from my.telegram.org
    API_ID = int(os.environ.get("API_ID", 0))  # REQUIRED: Your API ID from my.telegram.org

    API_HASH = os.environ.get("API_HASH", "")  # REQUIRED: Your API Hash from my.telegram.org

    # Get this value from @BotFather on Telegram
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")  # REQUIRED: Your bot token from @BotFather

    # Channel for logging and forcing user subscription
    # Example: "MyChannelUsername" (without the @)
    FORCE_SUB = os.environ.get("FORCE_SUB", "")  # OPTIONAL: Username of a channel to force users to join
    
    # Example: -1001234567890 (must be an integer)
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0)) # REQUIRED: A channel ID for logging bot activity

    # Bot Owner's Telegram User ID
    # Example: [123456789] (a list of integers)
    ADMIN = [int(admin) for admin in os.environ.get('ADMIN', '').split()] # REQUIRED: User ID of the bot admin

    # Aesthetics
    # A URL of a picture to show in the start message.
    START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/a00f9a250811b593b48b6.jpg")
