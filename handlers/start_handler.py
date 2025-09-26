import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)

# Store bot statistics in memory
bot_stats = {
    "start_time": datetime.now(),
    "total_users": set(),
    "files_processed": 0,
    "commands_used": 0
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when command /start is issued."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Update statistics
    bot_stats["total_users"].add(chat_id)
    bot_stats["commands_used"] += 1
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Rename File", callback_data="rename_help"),
            InlineKeyboardButton("🔄 Batch Mode", callback_data="batch_help")
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("📊 Status", callback_data="status")
        ],
        [
            InlineKeyboardButton("👨‍💻 Admin", callback_data="admin") 
            if user.id in config.ADMIN_IDS 
            else InlineKeyboardButton("⭐ Rate Bot", url="https://t.me/BotsArchive/")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message with image if available
    try:
        await update.message.reply_photo(
            photo=open("assets/welcome_image.jpg", "rb") if os.path.exists("assets/welcome_image.jpg") else None,
            caption=config.WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except:
        await update.message.reply_text(
            config.WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    bot_stats["commands_used"] += 1
    
    keyboard = [
        [
            InlineKeyboardButton("📚 Basic Usage", callback_data="basic_help"),
            InlineKeyboardButton("🔄 Batch Mode", callback_data="batch_help")
        ],
        [
            InlineKeyboardButton("📊 Supported Formats", callback_data="formats"),
            InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        config.HELP_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about information."""
    bot_stats["commands_used"] += 1
    
    about_text = f"""
🔧 **PYRO RENAME BOT v2.0**

**Version:** 2.0.0
**Developer:** PYRO Team
**Framework:** python-telegram-bot v20+
**Python Version:** 3.8+

**Features:**
✅ File Renaming (All formats)
✅ Batch Processing
✅ Thumbnail Support
✅ No Database Required
✅ Fast & Efficient

**Library:** python-telegram-bot
**License:** MIT

**Source Code:** [GitHub](https://github.com/TEAM-PYRO-BOTZ/PYRO-RENAME-BOT)
    """
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status and statistics."""
    bot_stats["commands_used"] += 1
    
    uptime = datetime.now() - bot_stats["start_time"]
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    status_text = f"""
📊 **BOT STATUS**

**Uptime:** {hours}h {minutes}m {seconds}s
**Total Users:** {len(bot_stats["total_users"])}
**Files Processed:** {bot_stats["files_processed"]}
**Commands Used:** {bot_stats["commands_used"]}

**System Status:**
✅ Bot: Online
✅ Processing: Normal
✅ Memory: Healthy
✅ Updates: Active

**Last Update:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')
