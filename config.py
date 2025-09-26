import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

class Config:
    """
    Configuration class to hold all the environment variables.
    """
    # Telegram API credentials
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")

    # Bot token from @BotFather
    BOT_TOKEN = os.environ.get("BOT_TOKEN")

    # Log channel/storage for files
    # This should be the ID of the channel where files will be forwarded/stored.
    # Make sure your bot is an admin in this channel.
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))

# Basic check to ensure essential variables are set
if not all([Config.API_ID, Config.API_HASH, Config.BOT_TOKEN, Config.LOG_CHANNEL]):
    raise RuntimeError(
        "One or more essential environment variables (API_ID, API_HASH, "
        "BOT_TOKEN, LOG_CHANNEL) are missing."
    )
