from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid
import logging
import sys
import asyncio
from config import Config

# Try different import approaches
try:
    from bot_handle import register_handlers
except ImportError as e:
    print(f"Import error: {e}")
    # Alternative import approach
    try:
        import bot_handle
        register_handlers = bot_handle.register_handlers
    except ImportError:
        print("Failed to import bot_handle. Please check the file exists.")
        sys.exit(1)

from web_server import start_web_server, stop_web_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
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
            workers=100,  # Increased for better performance
            max_concurrent_transmissions=10  # Better upload management
        )

        # Register all the handlers for the bot
        register_handlers(app)

        # Run the bot
        logger.info("Bot is starting...")
        await app.start()
        
        # Get bot info to confirm it's working
        me = await app.get_me()
        logger.info(f"Bot started successfully as @{me.username}")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
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
        try:
            await app.stop()
        except:
            pass
        print("Bot has stopped.")

if __name__ == "__main__":
    asyncio.run(main())
