# utils/helpers.py

import logging
import sys
from telegram import Update
from telegram.ext import ContextTypes

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and send a message to admins."""
    from config import config
    
    logger = logging.getLogger(__name__)
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Notify admin
    error_msg = f"⚠️ **Error Occurred**\n\n`{context.error}`"
    
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, 
                text=error_msg,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send error message to admin {admin_id}: {e}")
