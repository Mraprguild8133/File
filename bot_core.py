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
    """Setup all bot handlers with thumbnail support"""
    
    @client.on_message(filters.command("start"))
    async def turbo_start(_, message: Message):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Send File", callback_data="send_file")],
            [InlineKeyboardButton("🖼️ Thumbnail Info", callback_data="thumbnail_info")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        
        await message.reply_text(
            "🚀 **Turbo File Renamer Bot**\n\n"
            "• **Custom Thumbnail Support** ✅\n"
            "• **Complete Logging** ✅\n"
            "• **4GB File Support** ✅\n\n"
            "Send any file to get started!",
            reply_markup=keyboard
        )

    @client.on_message(filters.command("thumbnail"))
    async def thumbnail_info(_, message: Message):
        """Show thumbnail information"""
        uploader = file_processor.uploader
        thumb_status = "✅ **Custom Thumbnail Active**" if uploader.thumbnail else "❌ **No Thumbnail**"
        
        if uploader.thumbnail and os.path.exists(uploader.thumbnail):
            thumb_size = os.path.getsize(uploader.thumbnail)
            thumb_info = (
                f"{thumb_status}\n\n"
                f"**File:** `{os.path.basename(uploader.thumbnail)}`\n"
                f"**Size:** {format_bytes(thumb_size)}\n"
                f"**Dimensions:** {Config.THUMBNAIL_SIZE[0]}x{Config.THUMBNAIL_SIZE[1]}\n\n"
                f"To change thumbnail, replace `thumbnail.jpg` file."
            )
        else:
            thumb_info = (
                f"{thumb_status}\n\n"
                f"To add custom thumbnail:\n"
                f"1. Create a `thumbnail.jpg` file\n"
                f"2. Place it in bot directory\n"
                f"3. Restart the bot\n\n"
                f"Recommended size: 320x320 pixels"
            )
        
        await message.reply_text(thumb_info)

    @client.on_message(filters.command("logchannel"))
    async def log_channel_info(_, message: Message):
        """Show log channel information"""
        if Config.LOG_CHANNEL:
            try:
                chat = await client.get_chat(Config.LOG_CHANNEL)
                log_info = (
                    f"📊 **Log Channel Active** ✅\n\n"
                    f"**Channel:** {chat.title}\n"
                    f"**ID:** `{Config.LOG_CHANNEL}`\n"
                    f"**Logging:** All activities\n\n"
                    f"All file operations are being logged."
                )
            except:
                log_info = (
                    f"⚠️ **Log Channel Configured**\n\n"
                    f"**ID:** `{Config.LOG_CHANNEL}`\n"
                    f"**Status:** Cannot access channel\n"
                    f"Please check channel permissions."
                )
        else:
            log_info = (
                f"❌ **Log Channel Not Configured**\n\n"
                f"To enable logging:\n"
                f"1. Set LOG_CHANNEL in config\n"
                f"2. Add bot to channel as admin\n"
                f"3. Restart the bot"
            )
        
        await message.reply_text(log_info)

    @client.on_message(filters.document | filters.video | filters.audio)
    async def handle_file(client, message: Message):
        """Handle incoming files with thumbnail support"""
        user_id = message.from_user.id
        
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

        # Show file info with thumbnail status
        uploader = file_processor.uploader
        thumb_status = "✅ Custom thumbnail will be applied" if uploader.thumbnail else "⚠️ Using default thumbnail"
        
        await message.reply_text(
            f"📁 **File Received!** {thumb_status}\n\n"
            f"**File:** `{get_file_name(message)}`\n"
            f"**Size:** {format_bytes(file_size)}\n\n"
            "Please send the new filename (without extension):\n"
            "Example: `my_document`"
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
                "Example: `my_file`"
            )
            return

        # Process the file
        await process_file_rename(client, message, session, new_name)

    async def process_file_rename(client, message, session, new_name):
        """Process file renaming with enhanced feedback"""
        status_msg = await message.reply_text(
            f"⚡ **Processing Started**\n\n"
            f"**Thumbnail:** {'✅' if file_processor.uploader.thumbnail else '⚠️'}\n"
            f"**Logging:** {'✅' if Config.LOG_CHANNEL else '❌'}\n"
            f"**Status:** Initializing..."
        )
        
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
                
                success_msg = (
                    f"✅ **Processing Complete!**\n\n"
                    f"**File renamed successfully!**\n"
                    f"**Thumbnail:** {'✅ Applied' if file_processor.uploader.thumbnail else '⚠️ Default'}\n"
                    f"**Logged:** {'✅' if Config.LOG_CHANNEL else '❌'}\n"
                    f"**Thank you for using the bot!**"
                )
                await message.reply_text(success_msg)
            else:
                await status_msg.edit_text(f"❌ **Error:** {result['error']}")

        except Exception as e:
            await status_msg.edit_text(f"❌ **Processing failed:** {str(e)}")
        finally:
            # Cleanup session
            user_sessions.pop(message.from_user.id, None)

# Helper functions
async def check_rate_limit(user_id):
    """Check if user is within rate limits"""
    now = datetime.now()
    session = user_sessions.get(user_id, {})
    
    if session.get('last_reset_date') != now.date():
        session['files_today'] = 0
        session['last_reset_date'] = now.date()
    
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

def get_file_name(message):
    """Extract file name from message"""
    file_obj = message.document or message.video or message.audio
    return getattr(file_obj, 'file_name', 'file')

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
