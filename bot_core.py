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
# Track last message time per user to prevent spam
user_last_message = {}

def setup_bot_handlers(client: Client):
    """Setup all bot handlers with flood protection"""
    
    @client.on_message(filters.command("start"))
    async def turbo_start(_, message: Message):
        # Flood protection check
        if not await check_message_flood(message.from_user.id):
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Send File", callback_data="send_file")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        
        await message.reply_text(
            f"🚀 **Turbo File Renamer Bot**\n\n"
            f"• **Max Size:** {Config.MAX_FILE_SIZE // (1024**3)}GB\n"
            f"• **Speed:** Optimized\n"
            f"• **Updates:** Smart (anti-flood)\n\n"
            f"Send a file to begin!",
            reply_markup=keyboard
        )

    @client.on_message(filters.command("help"))
    async def turbo_help(_, message: Message):
        if not await check_message_flood(message.from_user.id):
            return
            
        await message.reply_text(
            "📖 **How to Use:**\n\n"
            "1. Send any file\n"
            "2. Enter new filename\n"
            "3. Wait for processing\n"
            "4. Get renamed file!\n\n"
            "⚡ **Anti-Flood System:**\n"
            "• Smart progress updates\n"
            "• Reduced API calls\n"
            "• Automatic wait handling"
        )

    @client.on_message(filters.document | filters.video | filters.audio)
    async def handle_file(client, message: Message):
        """Handle incoming files with flood protection"""
        user_id = message.from_user.id
        
        if not await check_message_flood(user_id):
            await message.reply_text("⏳ Please wait a moment before sending another file.")
            return

        # Rate limiting
        if not await check_rate_limit(user_id):
            await message.reply_text(
                "⏳ **Rate Limit Reached**\n\n"
                f"Limit: {Config.USER_RATE_LIMIT} files/hour\n"
                "Please wait before sending more files."
            )
            return

        # Check file size
        file_size = get_file_size(message)
        if file_size > Config.MAX_FILE_SIZE:
            await message.reply_text(
                f"❌ **File Too Large**\n\n"
                f"Max: {format_bytes(Config.MAX_FILE_SIZE)}\n"
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
            "Example: `my_document`"
        )

    @client.on_message(filters.text & filters.private)
    async def handle_filename(client, message: Message):
        """Handle filename input with flood protection"""
        user_id = message.from_user.id
        
        if not await check_message_flood(user_id):
            return
            
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
                "Example: `my_file`"
            )
            return

        # Process the file
        await process_file_rename(client, message, session, new_name)

    async def process_file_rename(client, message, session, new_name):
        """Process file renaming with error handling"""
        # Create a simple initial status message
        status_msg = await message.reply_text("⚡ **Processing your file...**")
        
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
                
                # Optional: Log to channel
                try:
                    if Config.LOG_CHANNEL:
                        await client.forward_messages(
                            Config.LOG_CHANNEL,
                            message.chat.id,
                            file_msg.id
                        )
                except:
                    pass
            else:
                await status_msg.edit_text(f"❌ **Error:** {result['error']}")

        except Exception as e:
            await status_msg.edit_text(f"❌ **Processing failed:** {str(e)}")
        finally:
            # Cleanup session
            user_sessions.pop(message.from_user.id, None)

async def check_message_flood(user_id):
    """Prevent message flooding"""
    now = time.time()
    last_time = user_last_message.get(user_id, 0)
    
    # Allow 1 message per 2 seconds
    if now - last_time < 2:
        return False
        
    user_last_message[user_id] = now
    return True

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
