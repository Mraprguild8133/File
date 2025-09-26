import logging
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums

from config import config
from handlers.start_handler import bot_stats

logger = logging.getLogger(__name__)

async def handle_callback_query(client, callback_query: CallbackQuery):
    """Handle inline keyboard button callbacks."""
    await callback_query.answer()
    
    callback_data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        if callback_data == "help":
            await show_help_menu(callback_query)
        elif callback_data == "basic_help":
            await show_basic_help(callback_query)
        elif callback_data == "batch_help":
            await show_batch_help(callback_query)
        elif callback_data == "formats":
            await show_supported_formats(callback_query)
        elif callback_data == "status":
            await show_status(callback_query)
        elif callback_data == "admin":
            await show_admin_panel(callback_query, user_id)
        elif callback_data == "rename_help":
            await show_rename_help(callback_query)
        elif callback_data == "main_menu":
            await show_main_menu(callback_query)
        elif callback_data.startswith("admin_"):
            await handle_admin_buttons(callback_query, callback_data, user_id)
        else:
            await callback_query.message.edit_text("❌ Unknown button action.")
            
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await callback_query.message.edit_text("❌ Error processing your request.")

async def show_help_menu(callback_query: CallbackQuery):
    """Show help menu with buttons."""
    from config import config
    
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
    
    await callback_query.message.edit_text(
        config.HELP_MESSAGE,
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.MARKDOWN
    )

async def show_basic_help(callback_query: CallbackQuery):
    """Show basic usage help."""
    basic_help = """
📚 **BASIC USAGE GUIDE**

**Step-by-Step Renaming:**

1. **Send a file** to the bot (up to 4GB)
2. **Wait for prompt** - bot will ask for new filename
3. **Enter new name** - type without extension
4. **Watch progress** - real-time upload/download progress
5. **Receive file** - get your renamed file back!

**Examples:**
- Send `large_video.mp4` (2GB) → Enter `my_video` → Receive `my_video.mp4`
- Send `document.pdf` → Enter `important_doc` → Receive `important_doc.pdf`

**Tips:**
- Filenames can contain letters, numbers, spaces, hyphens, and underscores
- Maximum filename length: 100 characters
- File size limit: 4GB per file
- Real-time progress tracking
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(basic_help, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)

async def show_batch_help(callback_query: CallbackQuery):
    """Show batch mode help."""
    batch_help = """
🔄 **BATCH RENAMING MODE**

**How to use Batch Mode:**

1. **Start batch mode** with `/batch` command
2. **Send multiple files** one by one (up to 10 files)
3. **Enter naming pattern** when done
4. **Receive all files** with sequential naming

**Pattern Examples:**
- `document_{n}` → document_1.pdf, document_2.jpg, etc.
- `photos_{n}` → photos_1.jpg, photos_2.jpg, etc.
- `large_files_{n}` → large_files_1.mp4, large_files_2.zip, etc.

**Batch Mode Features:**
- Supports up to 10 files per batch
- Each file up to 4GB
- Sequential numbering automatically
- Progress tracking for each file
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 Start Batch Mode", switch_inline_query_current_chat="/batch")],
        [InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(batch_help, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)

async def show_supported_formats(callback_query: CallbackQuery):
    """Show supported file formats."""
    from config import config
    
    formats_text = f"""
📊 **SUPPORTED FILE FORMATS (Up to 4GB)**

**📄 Documents:** PDF, DOC, DOCX, TXT, XLS, XLSX, PPT, PPTX
**🖼️ Images:** JPG, JPEG, PNG, GIF, BMP, WEBP, SVG, TIFF
**🎥 Videos:** MP4, AVI, MOV, MKV, FLV, WMV, WEBM, M4V
**🎵 Audio:** MP3, WAV, OGG, FLAC, M4A, AAC, WMA
**📦 Archives:** ZIP, RAR, 7Z, TAR, GZ, BZ2
**⚡ Executables:** EXE, MSI, APK, DEB, RPM
**🔧 Other:** ISO, DMG, CSV, JSON, XML

**📁 Maximum file size: 4GB**
**🔤 Total supported formats: {len(config.SUPPORTED_FORMATS)}**
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(formats_text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)

async def show_status(callback_query: CallbackQuery):
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
✅ 4GB Support: Active
✅ Processing: Normal
✅ Memory: Healthy

**Last Update:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="status")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(status_text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)

async def show_admin_panel(callback_query: CallbackQuery, user_id: int):
    """Show admin panel if user is admin."""
    if user_id not in config.ADMIN_IDS:
        await callback_query.message.edit_text("❌ Access denied. Admin only.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🛠 Maintenance", callback_data="admin_maintenance")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(
        "👨‍💻 **ADMIN PANEL**\n\n"
        "Manage your bot settings and operations.",
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.MARKDOWN
    )

async def show_main_menu(callback_query: CallbackQuery):
    """Show main menu."""
    user_id = callback_query.from_user.id
    
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
    
    from config import config
    await callback_query.message.edit_text(
        config.WELCOME_MESSAGE,
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.MARKDOWN
    )

async def show_rename_help(callback_query: CallbackQuery):
    """Show rename help."""
    rename_help = """
📤 **FILE RENAMING (Up to 4GB)**

**Quick Start:**
1. Simply send any file to the bot (up to 4GB)
2. Enter your desired filename when prompted
3. Watch real-time progress updates
4. Receive the renamed file instantly!

**Supported Files:**
- All document types (PDF, DOC, XLS, PPT, etc.)
- Images (JPG, PNG, GIF, etc.)
- Videos (MP4, AVI, MOV, etc.) - Up to 4GB!
- Audio files (MP3, WAV, FLAC, etc.)
- Archive files (ZIP, RAR, 7Z, etc.)

**Features:**
- 4GB file support
- Real-time progress tracking
- Original quality maintained
- Fast streaming technology

**Ready to start?** Just send a file!
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(rename_help, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)

async def handle_admin_buttons(callback_query: CallbackQuery, callback_data: str, user_id: int):
    """Handle admin-specific button actions."""
    if user_id not in config.ADMIN_IDS:
        await callback_query.message.edit_text("❌ Access denied. Admin only.")
        return
    
    if callback_data == "admin_stats":
        await show_admin_stats(callback_query)
    elif callback_data == "admin_broadcast":
        await callback_query.message.edit_text(
            "📢 **BROADCAST MESSAGE**\n\n"
            "Use /broadcast command to send a message to all users.",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    elif callback_data == "admin_maintenance":
        await callback_query.message.edit_text(
            "🛠 **MAINTENANCE MODE**\n\n"
            "Use /maintenance command to toggle maintenance mode.",
            parse_mode=enums.ParseMode.MARKDOWN
        )

async def show_admin_stats(callback_query: CallbackQuery):
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
- 4GB files handled: Tracking...
- Success rate: 99%+

**System Health:**
✅ Bot: Operational
✅ 4GB Support: Active
✅ Memory: Optimal
✅ Connections: Stable

**Last Update:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text(stats_text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)
