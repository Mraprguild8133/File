from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid
import logging
import sys
import asyncio
from config import Config
from bot_handle import register_handlers
from web_server import start_web_server, stop_web_server

# Turbo-optimized logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('turbo_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Turbo-optimized main function"""
    try:
        # Validate configuration
        if not all([Config.API_ID, Config.API_HASH, Config.BOT_TOKEN]):
            logger.error("Missing essential configuration")
            sys.exit(1)

        # Start web server
        logger.info("Starting turbo web server...")
        start_web_server()

        # Turbo-optimized client configuration
        app = Client(
            "turbo_file_renamer_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.MAX_WORKERS,
            max_concurrent_transmissions=Config.MAX_CONCURRENT_UPLOADS,
            sleep_threshold=30  # Reduced for faster response
        )

        # Register turbo handlers
        register_handlers(app)

        # Run with extreme speed
        logger.info("🚀 Starting Turbo Bot...")
        await app.start()
        
        # Get bot info
        me = await app.get_me()
        logger.info(f"Turbo Bot started successfully: @{me.username}")
        
        # Keep running
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
        await app.stop()
        print("🚀 Turbo Bot has stopped.")

if __name__ == "__main__":
    asyncio.run(main())
