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

# Message deduplication tracking
user_last_messages = {}
message_cooldown = 2  # seconds between messages per user

def setup_bot_handlers(client: Client):
    """Setup all bot handlers with duplicate prevention"""
    
    @client.on_message(filters.command("start"))
    async def turbo_start(_, message: Message):
        if not await check_message_duplicate(message.from_user.id):
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Send File", callback_data="send_file")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        
        await message.reply_text(
            "🚀 **Turbo File Renamer Bot**\n\n"
            "• **Anti-Duplicate System:** Active\n"
            "• **Smart Updates:** Every 5-6 seconds\n"
            "• **Flood Protection:** Enabled\n\n"
            "Send any file to get started!",
            reply_markup=keyboard
        )

    @client.on_message(filters.command("help"))
    async def turbo_help(_, message: Message):
        if not await check_message_duplicate(message.from_user.id):
            return
            
        await message.reply_text(
            "📖 **Anti-Duplicate System**\n\n"
            "To prevent flooding and duplicate messages:\n"
            "• Progress updates every 5-6 seconds only\n"
            "• Messages only when content actually changes\n"
            "• Cooldown between user messages\n"
            "• Smart rate limiting\n\n"
            "This ensures smooth operation without errors!"
        )

    @client.on_message(filters.document | filters.video | filters.audio)
    async def handle_file(client, message: Message):
        """Handle incoming files with duplicate prevention"""
        user_id = message.from_user.id
        
        if not await check_message_duplicate(user_id):
            return

        # Rate limiting
        if not await check_rate_limit(user_id):
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
            'waiting_for_name': True,
            'last_update': time.time()
        }

        await message.reply_text(
            "📁 **File Received!**\n\n"
            "Please send the new filename (without extension):\n"
            "Example: `my_document`"
        )

    @client.on_message(filters.text & filters.private)
    async def handle_filename(client, message: Message):
        """Handle filename input with duplicate prevention"""
        user_id = message.from_user.id
        
        if not await check_message_duplicate(user_id):
            return
            
        session = user_sessions.get(user_id)

        if not session or not session.get('waiting_for_name'):
            # Check if we recently sent this message
            last_msg = user_last_messages.get(user_id, {}).get('last_response')
            if last_msg != "send_file_first":
                await message.reply_text("📁 Please send a file first!")
                user_last_messages[user_id] = {
                    'last_response': "send_file_first",
                    'timestamp': time.time()
                }
            return

        new_name = message.text.strip()
        if not is_valid_filename(new_name):
            # Check if we recently sent this error
            last_msg = user_last_messages.get(user_id, {}).get('last_response')
            if last_msg != "invalid_filename":
                await message.reply_text(
                    "❌ **Invalid Filename**\n\n"
                    "Please use a valid filename:\n"
                    "• No special characters\n"
                    "• Max 100 characters"
                )
                user_last_messages[user_id] = {
                    'last_response': "invalid_filename",
                    'timestamp': time.time()
                }
            return

        # Process the file
        await process_file_rename(client, message, session, new_name)

    async def process_file_rename(client, message, session, new_name):
        """Process file renaming with duplicate prevention"""
        # Create initial status message
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
                
                # Log to channel if configured
                try:
                    if Config.LOG_CHANNEL:
                        await client.forward_messages(
                            Config.LOG_CHANNEL,
                            message.chat.id,
                            file_msg.id
                        )
                except:
                    pass
                    
                # Send success message (only if different)
                success_msg = "✅ **File processing completed successfully!**"
                if user_last_messages.get(user_id, {}).get('last_response') != "success":
                    await message.reply_text(success_msg)
                    user_last_messages[user_id] = {
                        'last_response': "success",
                        'timestamp': time.time()
                    }
            else:
                error_msg = f"❌ **Error:** {result['error']}"
                if user_last_messages.get(user_id, {}).get('last_response') != error_msg:
                    await status_msg.edit_text(error_msg)
                    user_last_messages[user_id] = {
                        'last_response': error_msg,
                        'timestamp': time.time()
                    }

        except Exception as e:
            error_msg = f"❌ **Processing failed:** {str(e)}"
            if user_last_messages.get(user_id, {}).get('last_response') != error_msg:
                await status_msg.edit_text(error_msg)
                user_last_messages[user_id] = {
                    'last_response': error_msg,
                    'timestamp': time.time()
                }
        finally:
            # Cleanup session
            user_sessions.pop(message.from_user.id, None)

async def check_message_duplicate(user_id):
    """Prevent duplicate messages from same user"""
    now = time.time()
    user_data = user_last_messages.get(user_id, {})
    last_time = user_data.get('timestamp', 0)
    
    # Allow 1 message per cooldown period
    if now - last_time < message_cooldown:
        return False
        
    user_last_messages[user_id] = {
        'timestamp': now,
        'last_response': user_data.get('last_response', '')
    }
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
            # Only send rate limit message once per violation
            if user_last_messages.get(user_id, {}).get('last_response') != "rate_limit":
                await message.reply_text(
                    "⏳ **Rate Limit Reached**\n\n"
                    f"Limit: {Config.USER_RATE_LIMIT} files/hour\n"
                    "Please wait before sending more files."
                )
                user_last_messages[user_id] = {
                    'last_response': "rate_limit",
                    'timestamp': time.time()
                }
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
