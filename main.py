import os
import logging
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ForceReply
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import FloodWait, RPCError

from config import config
from handlers.start_handler import start_command, help_command, about_command, status_command
from handlers.rename_handler import (
    handle_file_message, handle_rename_text, handle_batch_start,
    handle_batch_files, handle_batch_pattern, cancel_command
)
from handlers.admin_handler import admin_panel, bot_stats, broadcast_command
from handlers.callback_handler import handle_callback_query
from utils.helpers import setup_logging, error_handler
from utils.file_utils import ensure_directories

# Global variables
app = None
user_sessions = {}

class Progress:
    """Progress tracker for large file operations"""
    def __init__(self, message: Message, operation: str, total_size: int):
        self.message = message
        self.operation = operation
        self.total_size = total_size
        self.processed = 0
        self.last_update = 0
        self.update_interval = config.PROGRESS_UPDATE_INTERVAL

    async def update(self, processed: int):
        self.processed = processed
        current_time = asyncio.get_event_loop().time()
        
        # Update progress only at intervals to avoid flooding
        if (current_time - self.last_update > 5 or 
            processed - self.last_update >= self.update_interval or 
            processed == self.total_size):
            
            percentage = (processed / self.total_size) * 100
            progress_bar = self.create_progress_bar(percentage)
            speed = self.calculate_speed(processed)
            
            text = (
                f"🔄 **{self.operation} Progress**\n\n"
                f"📊 **Progress:** {percentage:.1f}%\n"
                f"📈 **Bar:** {progress_bar}\n"
                f"📁 **Processed:** {self.format_size(processed)} / {self.format_size(self.total_size)}\n"
                f"⚡ **Speed:** {speed}/s\n"
                f"⏱️ **Time:** {self.calculate_eta(processed)}"
            )
            
            try:
                await self.message.edit_text(text)
                self.last_update = processed
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except RPCError:
                pass

    def create_progress_bar(self, percentage: float) -> str:
        bars = 10
        filled_bars = int(bars * percentage / 100)
        empty_bars = bars - filled_bars
        return "█" * filled_bars + "░" * empty_bars

    def format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def calculate_speed(self, processed: int) -> str:
        # Simple speed calculation (can be enhanced with time tracking)
        return self.format_size(processed / max(asyncio.get_event_loop().time(), 1))

    def calculate_eta(self, processed: int) -> str:
        if processed == 0:
            return "Calculating..."
        remaining = self.total_size - processed
        speed = processed / max(asyncio.get_event_loop().time(), 1)
        if speed > 0:
            eta_seconds = remaining / speed
            return f"{eta_seconds:.0f}s"
        return "Unknown"

async def start_bot():
    """Initialize and start the bot"""
    global app
    
    # Ensure directories exist
    ensure_directories()
    
    # Create Pyrogram client
    app = Client(
        "pyro_rename_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        workers=100,  # Increased workers for large files
        workdir=os.getcwd(),
        sleep_threshold=60
    )
    
    # Register handlers
    register_handlers(app)
    
    # Start the bot
    await app.start()
    
    # Get bot info
    me = await app.get_me()
    print(f"""
    🤖 PYRO RENAME BOT v3.0 Started!
    
    ██████╗ ██╗   ██╗██████╗  ██████╗
    ██╔══██╗╚██╗ ██╔╝██╔══██╗██╔═══██╗
    ██████╔╝ ╚████╔╝ ██████╔╝██║   ██║
    ██╔═══╝   ╚██╔╝  ██╔══██╗██║   ██║
    ██║        ██║   ██████╔╝╚██████╔╝
    ╚═╝        ╚═╝   ╚═════╝  ╚═════╝
    
    🤖 Bot: @{me.username}
    🚀 Version: 3.0.0
    📁 Max File Size: 4GB
    ⚡ Framework: Pyrogram
    🔧 API ID: {config.API_ID}
    """)
    
    # Keep the bot running
    await asyncio.Event().wait()

def register_handlers(client: Client):
    """Register all message and callback handlers"""
    
    # Command handlers
    client.add_handler(MessageHandler(start_command, filters.command("start")))
    client.add_handler(MessageHandler(help_command, filters.command("help")))
    client.add_handler(MessageHandler(about_command, filters.command("about")))
    client.add_handler(MessageHandler(status_command, filters.command("status")))
    client.add_handler(MessageHandler(admin_panel, filters.command("admin")))
    client.add_handler(MessageHandler(bot_stats, filters.command("stats")))
    client.add_handler(MessageHandler(broadcast_command, filters.command("broadcast")))
    client.add_handler(MessageHandler(handle_batch_start, filters.command("batch")))
    client.add_handler(MessageHandler(cancel_command, filters.command("cancel")))
    
    # File message handler
    client.add_handler(MessageHandler(
        handle_file_message, 
        filters.document | filters.photo | filters.video | filters.audio
    ))
    
    # Text message handler (for filename input)
    client.add_handler(MessageHandler(
        handle_rename_text,
        filters.text & ~filters.command
    ))
    
    # Callback query handler
    client.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Error handler
    client.add_error_handler(error_handler)

async def download_file_with_progress(
    message: Message, 
    file_id: str, 
    file_name: str, 
    file_size: int
) -> str:
    """Download file with progress updates"""
    progress_msg = await message.reply_text("🔄 Starting download...")
    progress = Progress(progress_msg, "Downloading", file_size)
    
    download_path = os.path.join(config.DOWNLOAD_PATH, file_name)
    
    try:
        # Create download task with progress
        await app.download_media(
            message=file_id,
            file_name=download_path,
            progress=progress.update,
            progress_args=(progress,)
        )
        
        await progress_msg.edit_text("✅ Download completed!")
        return download_path
        
    except Exception as e:
        await progress_msg.edit_text(f"❌ Download failed: {str(e)}")
        return None

async def upload_file_with_progress(
    message: Message,
    file_path: str,
    caption: str,
    thumb: str = None
) -> bool:
    """Upload file with progress updates"""
    file_size = os.path.getsize(file_path)
    progress_msg = await message.reply_text("🔄 Starting upload...")
    progress = Progress(progress_msg, "Uploading", file_size)
    
    try:
        # Determine file type and send appropriately
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
            await app.send_photo(
                chat_id=message.chat.id,
                photo=file_path,
                caption=caption,
                progress=progress.update,
                progress_args=(progress,)
            )
        elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
            await app.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=caption,
                thumb=thumb,
                progress=progress.update,
                progress_args=(progress,)
            )
        elif file_path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
            await app.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=caption,
                progress=progress.update,
                progress_args=(progress,)
            )
        else:
            await app.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=caption,
                thumb=thumb,
                progress=progress.update,
                progress_args=(progress,)
            )
        
        await progress_msg.delete()
        return True
        
    except Exception as e:
        await progress_msg.edit_text(f"❌ Upload failed: {str(e)}")
        return False

async def main():
    """Main function to start the bot"""
    try:
        await start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logging.error(f"Bot startup error: {e}")
    finally:
        if app:
            await app.stop()

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Run the bot
    asyncio.run(main())
