import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from file_processor import TurboFileProcessor
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# User session management
user_sessions = {}
file_processor = TurboFileProcessor()

def setup_bot_handlers(client: Client):
    """Setup all bot handlers"""
    
    @client.on_message(filters.command("start"))
    async def turbo_start(_, message: Message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Send File", callback_data="send_file")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        
        await message.reply_text(
            f"🚀 **Turbo File Renamer Bot**\n\n"
            f"• **Max File Size:** {Config.MAX_FILE_SIZE // (1024**3)}GB\n"
            f"• **Speed:** Ultra Turbo Mode\n"
            f"• **Thumbnail:** Custom Support\n\n"
            f"Send any file to get started!",
            reply_markup=keyboard
        )

    @client.on_message(filters.command("help"))
    async def turbo_help(_, message: Message):
        await message.reply_text(
            "📖 **How to Use:**\n\n"
            "1. Send any file (document/video/audio)\n"
            "2. Enter new filename when asked\n"
            "3. Wait for turbo processing\n"
            "4. Get your renamed file!\n\n"
            "⚡ **Features:**\n"
            "• 4GB file support\n"
            "• Custom thumbnails\n"
            "• Extreme speed\n"
            "• Progress tracking\n\n"
            "Just send a file to begin!"
        )

    # ... rest of the bot_core.py code remains the same ...
    # (Keep all the other functions as they were)
    @client.on_message(filters.command("stats"))
    async def user_stats(_, message: Message):
        user_id = message.from_user.id
        stats = user_sessions.get(user_id, {})
        files_today = stats.get('files_today', 0)
        
        await message.reply_text(
            f"📊 **Your Stats**\n"
            f"• Files today: {files_today}\n"
            f"• Hourly limit: {Config.USER_RATE_LIMIT}\n"
            f"• Status: ✅ Active"
        )

    @client.on_message(filters.document | filters.video | filters.audio)
    async def handle_file(client, message: Message):
        """Handle incoming files with turbo speed"""
        user_id = message.from_user.id
        
        # Rate limiting
        if not await check_rate_limit(user_id):
            await message.reply_text(
                "⏳ **Rate Limit Reached**\n\n"
                f"You can process {Config.USER_RATE_LIMIT} files per hour.\n"
                "Please wait a while before sending more files."
            )
            return

        # Check file size
        file_size = get_file_size(message)
        if file_size > Config.MAX_FILE_SIZE:
            await message.reply_text(
                f"❌ **File Too Large**\n\n"
                f"Max size: {format_bytes(Config.MAX_FILE_SIZE)}\n"
                f"Your file: {format_bytes(file_size)}"
            )
            return

        # Store file info
        user_sessions[user_id] = {
            'file_message': message,
            'file_size': file_size,
            'received_time': datetime.now(),
            'waiting_for_name': True
        }

        await message.reply_text(
            "📁 **File Received!**\n\n"
            "Please send the new filename (without extension):\n"
            "Example: `my_important_document`"
        )

    @client.on_message(filters.text & filters.private)
    async def handle_filename(client, message: Message):
        """Handle filename input"""
        user_id = message.from_user.id
        session = user_sessions.get(user_id)

        if not session or not session.get('waiting_for_name'):
            await message.reply_text("📁 Please send a file first!")
            return

        new_name = message.text.strip()
        if not is_valid_filename(new_name):
            await message.reply_text(
                "❌ **Invalid Filename**\n\n"
                "Please use a valid filename:\n"
                "• No special characters\n"
                "• Max 100 characters\n"
                "• Example: `my_file_2024`"
            )
            return

        # Process the file
        await process_file_rename(client, message, session, new_name)

    async def process_file_rename(client, message, session, new_name):
        """Process file renaming with turbo speed"""
        status_msg = await message.reply_text("⚡ **Starting Turbo Processing...**")
        
        try:
            file_msg = session['file_message']
            result = await file_processor.process_file(
                client=client,
                file_message=file_msg,
                new_filename=new_name,
                status_message=status_msg,
                chat_id=message.chat.id
            )

            if result['success']:
                # Update user stats
                user_id = message.from_user.id
                if 'files_today' not in user_sessions[user_id]:
                    user_sessions[user_id]['files_today'] = 0
                user_sessions[user_id]['files_today'] += 1
                
                # Log to channel
                await client.forward_messages(
                    Config.LOG_CHANNEL,
                    message.chat.id,
                    file_msg.id
                )
            else:
                await status_msg.edit_text(f"❌ **Error:** {result['error']}")

        except Exception as e:
            await status_msg.edit_text(f"❌ **Processing failed:** {str(e)}")
        finally:
            # Cleanup session
            user_sessions.pop(message.from_user.id, None)

async def check_rate_limit(user_id):
    """Check if user is within rate limits"""
    now = datetime.now()
    session = user_sessions.get(user_id, {})
    
    # Reset daily counter if new day
    if session.get('last_reset_date') != now.date():
        session['files_today'] = 0
        session['last_reset_date'] = now.date()
    
    # Check hourly limit
    last_file_time = session.get('last_file_time')
    if last_file_time and (now - last_file_time) < timedelta(hours=1):
        file_count = session.get('files_this_hour', 0)
        if file_count >= Config.USER_RATE_LIMIT:
            return False
        session['files_this_hour'] = file_count + 1
    else:
        session['files_this_hour'] = 1
        session['last_file_time'] = now
    
    user_sessions[user_id] = session
    return True

def get_file_size(message):
    """Extract file size from message"""
    file_obj = message.document or message.video or message.audio
    return getattr(file_obj, 'file_size', 0)

def is_valid_filename(name):
    """Validate filename"""
    if not name or len(name) > 100:
        return False
    invalid_chars = '<>:"/\\|?*'
    return not any(char in name for char in invalid_chars)

def format_bytes(size):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"
