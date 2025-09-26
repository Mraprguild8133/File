import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import config
from handlers.start_handler import bot_stats

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel for bot management."""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🛠 Maintenance", callback_data="admin_maintenance")],
        [InlineKeyboardButton("🔄 Restart", callback_data="admin_restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👨‍💻 **ADMIN PANEL**\n\n"
        "Manage your bot settings and operations.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed bot statistics for admin."""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    uptime = datetime.now() - bot_stats["start_time"]
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    stats_text = f"""
📈 **ADMIN STATISTICS**

**Bot Uptime:** {hours}h {minutes}m {seconds}s
**Total Users:** {len(bot_stats["total_users"])}
**Files Processed:** {bot_stats["files_processed"]}
**Commands Used:** {bot_stats["commands_used"]}

**Memory Usage:**
• Active Sessions: {len(user_sessions)}
• Total Storage: Calculating...

**Performance:**
• Uptime: {uptime.total_seconds():.0f} seconds
• Average files/day: Calculating...

**Last Update:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast message process."""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📢 **BROADCAST MESSAGE**\n\n"
        "Please enter the message you want to broadcast to all users:\n"
        "Type /cancel to abort.",
        parse_mode='Markdown'
    )
    
    return BROADCAST

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message sending."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return ConversationHandler.END
    
    await update.message.reply_text("⏳ Broadcasting message...")
    
    # Send to all users (simplified - in production, you'd want pagination)
    success_count = 0
    error_count = 0
    
    for chat_id in bot_stats["total_users"]:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 **Announcement from Admin:**\n\n{message_text}",
                parse_mode='Markdown'
            )
            success_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            error_count += 1
            logger.error(f"Error broadcasting to {chat_id}: {e}")
    
    await update.message.reply_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Success: {success_count} users\n"
        f"❌ Failed: {error_count} users",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle maintenance mode."""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    # Toggle maintenance mode (implementation depends on your needs)
    await update.message.reply_text("🛠 Maintenance mode toggled.")
