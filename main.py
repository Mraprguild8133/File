import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)

from config import config
from handlers.start_handler import start, help_command, about_command, status_command
from handlers.rename_handler import (
    handle_file, handle_rename_text, handle_batch_start,
    handle_batch_files, handle_batch_pattern, cancel_command
)
from handlers.admin_handler import (
    admin_panel, bot_stats, broadcast_command, 
    handle_broadcast_message, maintenance_mode
)
from handlers.callback_handler import button_handler
from utils.helpers import setup_logging, error_handler

# Conversation states
RENAME, BATCH_MODE, BROADCAST = range(3)

def main():
    """Start the bot."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create Application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add conversation handler for file renaming
    rename_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,
                handle_file
            )
        ],
        states={
            RENAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rename_text)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True
    )
    
    # Batch renaming conversation
    batch_conv = ConversationHandler(
        entry_points=[CommandHandler("batch", handle_batch_start)],
        states={
            BATCH_MODE: [
                MessageHandler(
                    filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,
                    handle_batch_files
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_pattern)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    # Admin broadcast conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_command)],
        states={
            BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("stats", bot_stats))
    application.add_handler(CommandHandler("maintenance", maintenance_mode))
    
    application.add_handler(rename_conv)
    application.add_handler(batch_conv)
    application.add_handler(broadcast_conv)
    
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    if config.DEBUG:
        logger.info("🤖 Bot starting in DEVELOPMENT mode...")
    else:
        logger.info("🚀 Bot starting in PRODUCTION mode...")
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
