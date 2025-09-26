from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid
import logging
import sys
from config import Config
from bot_handle import register_handlers
from web_server import start_web_server, stop_web_server  # Add this import

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    The main function to start the bot with web server support.
    """
    try:
        # Validate essential configuration
        if not all([Config.API_ID, Config.API_HASH, Config.BOT_TOKEN]):
            logger.error("Missing essential configuration")
            sys.exit(1)

        # Start web server
        logger.info("Starting web server on port 5000...")
        web_server_started = start_web_server()
        
        if web_server_started:
            logger.info("Web server started successfully")
        else:
            logger.warning("Failed to start web server")

        # Initialize the Pyrogram Client
        app = Client(
            "file_renamer_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=20
        )

        # Register all the handlers for the bot
        register_handlers(app)

        # Run the bot
        logger.info("Bot is starting...")
        app.run()
        
    except (ApiIdInvalid, AccessTokenInvalid) as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Cleaning up...")
        stop_web_server()
        print("Bot has stopped.")

if __name__ == "__main__":
    main()
