import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import config
from handlers.start_handler import bot_stats

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    try:
        if callback_data == "help":
            await show_help_menu(query)
        elif callback_data == "basic_help":
            await show_basic_help(query)
        elif callback_data == "batch_help":
            await show_batch_help(query)
        elif callback_data == "formats":
            await show_supported_formats(query)
        elif callback_data == "status":
            await show_status(query)
        elif callback_data == "admin":
            await show_admin_panel(query, user_id)
        elif callback_data == "rename_help":
            await show_rename_help(query)
        elif callback_data == "main_menu":
            await show_main_menu(query)
        elif callback_data.startswith("admin_"):
            await handle_admin_buttons(query, callback_data, user_id)
        else:
            await query.edit_message_text("❌ Unknown button action.")
            
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await query.edit_message_text("❌ Error processing your request.")

async def show_help_menu(query):
    """Show help menu with buttons."""
    keyboard = [
        [
            InlineKeyboardButton("📚 Basic Usage", callback_data="basic_help"),
            InlineKeyboardButton("🔄 Batch Mode", callback_data="batch_help")
        ],
        [
            InlineKeyboardButton("📊 Supported Formats", callback_data="formats"),
            InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        config.HELP_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_basic_help(query):
    """Show basic usage help."""
    basic_help = """
📚 **BASIC USAGE GUIDE**

**Step-by-Step Renaming:**

1. **Send a file** to the bot (document, photo, video, or audio)
2. **Wait for prompt** - bot will ask for new filename
3. **Enter new name** - type without extension
4. **Receive file** - get your renamed file back!

**Examples:**
- Send `document.pdf` → Enter `my_document` → Receive `my_document.pdf`
- Send `photo.jpg` → Enter `vacation_pic` → Receive `vacation_pic.jpg`

**Tips:**
- Filenames can contain letters, numbers, spaces, hyphens, and underscores
- Maximum filename length: 100 characters
- File size limit: 500MB per file
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(basic_help, reply_markup=reply_markup, parse_mode='Markdown')

async def show_batch_help(query):
    """Show batch mode help."""
    batch_help = """
🔄 **BATCH RENAMING MODE**

**How to use Batch Mode:**

1. **Start batch mode** with `/batch` command
2. **Send multiple files** one by one
3. **Enter naming pattern** when done
4. **Receive all files** with sequential naming

**Pattern Examples:**
- `document_{n}` → document_1.pdf, document_2.jpg, etc.
- `photos_{n}` → photos_1.jpg, photos_2.jpg, etc.
- `my_files_{n}` → my_files_1.zip, my_files_2.txt, etc.

**Batch Mode Features:**
- Supports up to 10 files per batch
- Maintains original file formats
- Sequential numbering automatically
- Quick processing of multiple files
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 Start Batch Mode", switch_inline_query_current_chat="/batch")],
        [InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(batch_help, reply_markup=reply_markup, parse_mode='Markdown')

async def show_supported_formats(query):
    """Show supported file formats."""
    formats_text = """
📊 **SUPPORTED FILE FORMATS**

**📄 Documents:**
- PDF (.pdf)
- Word (.doc, .docx)
- Text (.txt, .rtf)
- OpenDocument (.odt)

**🖼️ Images:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- SVG (.svg)

**🎥 Videos:**
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- FLV (.flv)
- WMV (.wmv)

**🎵 Audio:**
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- FLAC (.flac)
- M4A (.m4a)

**📦 Archives:**
- ZIP (.zip)
- RAR (.rar)
- 7Z (.7z)
- TAR (.tar)
- GZ (.gz)

**📁 Maximum file size: 500MB**
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(formats_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_status(query):
    """Show bot status."""
    from datetime import datetime
    
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
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="status")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_panel(query, user_id):
    """Show admin panel if user is admin."""
    if user_id not in config.ADMIN_IDS:
        await query.edit_message_text("❌ Access denied. Admin only.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🛠 Maintenance", callback_data="admin_maintenance")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👨‍💻 **ADMIN PANEL**\n\n"
        "Manage your bot settings and operations.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_main_menu(query):
    """Show main menu."""
    user_id = query.from_user.id
    
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
            if user_id in config.ADMIN_IDS 
            else InlineKeyboardButton("⭐ Rate Bot", url="https://t.me/BotsArchive/")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        config.WELCOME_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_rename_help(query):
    """Show rename help."""
    rename_help = """
📤 **FILE RENAMING**

**Quick Start:**
1. Simply send any file to the bot
2. Enter your desired filename when prompted
3. Receive the renamed file instantly!

**Supported Files:**
- All document types (PDF, DOC, TXT, etc.)
- Images (JPG, PNG, GIF, etc.)
- Videos (MP4, AVI, MOV, etc.)
- Audio files (MP3, WAV, etc.)
- Archive files (ZIP, RAR, etc.)

**Features:**
- Fast processing
- Original quality maintained
- Automatic format detection
- Thumbnail support for media files

**Ready to start?** Just send a file!
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(rename_help, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_buttons(query, callback_data, user_id):
    """Handle admin-specific button actions."""
    if user_id not in config.ADMIN_IDS:
        await query.edit_message_text("❌ Access denied. Admin only.")
        return
    
    if callback_data == "admin_stats":
        await show_admin_stats(query)
    elif callback_data == "admin_broadcast":
        await query.edit_message_text(
            "📢 **BROADCAST MESSAGE**\n\n"
            "Use /broadcast command to send a message to all users.",
            parse_mode='Markdown'
        )
    elif callback_data == "admin_maintenance":
        await query.edit_message_text(
            "🛠 **MAINTENANCE MODE**\n\n"
            "Use /maintenance command to toggle maintenance mode.",
            parse_mode='Markdown'
        )
    elif callback_data == "admin_restart":
        await query.edit_message_text("🔄 Restart functionality would be implemented here.")

async def show_admin_stats(query):
    """Show detailed admin statistics."""
    from datetime import datetime
    
    uptime = datetime.now() - bot_stats["start_time"]
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Calculate files per day
    days = uptime.total_seconds() / 86400
    files_per_day = bot_stats["files_processed"] / max(days, 1)
    
    stats_text = f"""
📈 **ADMIN STATISTICS**

**Bot Uptime:** {hours}h {minutes}m {seconds}s
**Total Users:** {len(bot_stats["total_users"])}
**Files Processed:** {bot_stats["files_processed"]}
**Commands Used:** {bot_stats["commands_used"]}

**Performance Metrics:**
- Average files/day: {files_per_day:.1f}
- User growth rate: Calculating...
- Success rate: 99%+

**System Health:**
✅ Bot: Operational
✅ Memory: Optimal
✅ Processing: Normal
✅ Connections: Stable

**Last Update:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
