from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid
import logging
import sys
import asyncio
from config import Config

# Import handlers
from bot_core import setup_bot_handlers

# Turbo logging
logging.basicConfig(
    level=logging.INFO,
    format='⚡ %(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('turbo_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TurboBot:
    def __init__(self):
        self.client = None
        self.is_running = False

    async def initialize(self):
        """Initialize the turbo bot"""
        try:
            # Validate config
            if not all([Config.API_ID, Config.API_HASH, Config.BOT_TOKEN]):
                logger.error("❌ Missing API configuration")
                return False

            # Create client with turbo settings
            self.client = Client(
                "turbo_file_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN,
                workers=Config.MAX_WORKERS,
                max_concurrent_transmissions=Config.MAX_CONCURRENT_UPLOADS,
                sleep_threshold=10  # Faster response
            )

            # Setup handlers
            setup_bot_handlers(self.client)
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    async def start_bot(self):
        """Start the turbo bot"""
        try:
            await self.client.start()
            bot_info = await self.client.get_me()
            logger.info(f"🚀 Turbo Bot started: @{bot_info.username}")
            logger.info(f"⚡ Workers: {Config.MAX_WORKERS}")
            logger.info(f"📁 Max file size: {Config.MAX_FILE_SIZE // (1024**3)}GB")
            
            self.is_running = True
            return True
            
        except (ApiIdInvalid, AccessTokenInvalid) as e:
            logger.error(f"❌ Auth error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Startup error: {e}")
            return False

    async def run(self):
        """Main bot runner"""
        if not await self.initialize():
            return

        if not await self.start_bot():
            return

        try:
            # Keep bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Runtime error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        if self.client:
            await self.client.stop()
        logger.info("🔴 Turbo Bot stopped")

async def main():
    """Entry point"""
    bot = TurboBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
