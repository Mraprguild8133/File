import os
import logging
import asyncio
from datetime import datetime
from pyrogram.types import Message, ForceReply
from pyrogram import filters, Client

from config import config
from utils.file_utils import (
    get_file_extension, is_file_supported,
    get_file_size, create_thumbnail, cleanup_file
)

logger = logging.getLogger(__name__)

# Store user sessions globally (simplified for this example)
user_sessions = {}

async def handle_file_message(client: Client, message: Message):
    """Handle incoming files for renaming"""
    try:
        user_id = message.from_user.id
        
        # Get file information based on message type
        if message.document:
            file = message.document
            file_name = file.file_name
            file_size = file.file_size
            mime_type = file.mime_type
        elif message.photo:
            file = message.photo
            file_name = "photo.jpg"
            file_size = message.photo.file_size
            mime_type = "image/jpeg"
        elif message.video:
            file = message.video
            file_name = getattr(file, 'file_name', 'video.mp4')
            file_size = file.file_size
            mime_type = "video/mp4"
        elif message.audio:
            file = message.audio
            file_name = getattr(file, 'file_name', 'audio.mp3')
            file_size = file.file_size
            mime_type = "audio/mpeg"
        else:
            await message.reply_text("❌ Unsupported file type.")
            return

        # Check file size (4GB limit)
        if file_size > config.MAX_FILE_SIZE:
            await message.reply_text(
                f"❌ File too large! Maximum size is 4GB.\n"
                f"Your file: {get_file_size(file_size)}"
            )
            return

        # Check supported format
        extension = get_file_extension(file_name)
        if not is_file_supported(extension):
            await message.reply_text(
                f"❌ File format '.{extension}' is not supported.\n\n"
                f"✅ Supported formats: {', '.join(sorted(config.SUPPORTED_FORMATS))}"
            )
            return

        # Store file info for renaming
        user_sessions[user_id] = {
            'file_id': message.id,
            'original_name': file_name,
            'mime_type': mime_type,
            'file_size': file_size,
            'extension': extension,
            'timestamp': datetime.now(),
            'chat_id': message.chat.id
        }

        # Ask for new filename with ForceReply
        await message.reply_text(
            f"📁 **File Received Successfully!**\n\n"
            f"📝 **File:** `{file_name}`\n"
            f"📊 **Size:** {get_file_size(file_size)}\n"
            f"🔤 **Format:** {extension.upper()}\n\n"
            "💬 **Please send the new filename (without extension):**\n"
            "Type /cancel to abort.",
            reply_markup=ForceReply(selective=True),
            parse_mode=enums.ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await message.reply_text("❌ Error processing your file.")

async def handle_rename_text(client: Client, message: Message):
    """Handle the new filename input"""
    try:
        user_id = message.from_user.id
        
        if user_id not in user_sessions:
            await message.reply_text("❌ No file found. Please send a file first.")
            return

        session = user_sessions[user_id]
        new_filename = message.text.strip()

        # Validate filename
        if not new_filename or len(new_filename) > 100:
            await message.reply_text(
                "❌ Invalid filename. Please enter a valid name (max 100 characters).\n"
                "💬 Please try again:"
            )
            return

        # Clean filename
        import re
        new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename).strip()
        
        if not new_filename:
            await message.reply_text("❌ Please provide a valid filename.")
            return

        new_filename_with_ext = f"{new_filename}.{session['extension']}"

        # Download the file with progress
        from bot import download_file_with_progress, upload_file_with_progress
        
        download_path = await download_file_with_progress(
            message, session['file_id'], session['original_name'], session['file_size']
        )
        
        if not download_path:
            return

        # Create thumbnail for media files
        thumbnail_path = None
        if session['mime_type'].startswith(('image/', 'video/')):
            thumbnail_path = create_thumbnail(download_path, config.THUMBNAIL_SIZE)

        # Prepare caption
        processing_time = (datetime.now() - session['timestamp']).total_seconds()
        caption = (
            f"✅ **Renamed Successfully!**\n\n"
            f"📁 **Original:** `{session['original_name']}`\n"
            f"📝 **New:** `{new_filename_with_ext}`\n"
            f"📊 **Size:** {get_file_size(session['file_size'])}\n"
            f"⏰ **Processed in:** {processing_time:.1f}s\n"
            f"🔧 **By:** @{client.me.username}"
        )

        # Upload the renamed file with progress
        success = await upload_file_with_progress(
            message, download_path, caption, thumbnail_path
        )

        if success:
            # Update statistics
            from handlers.start_handler import bot_stats
            bot_stats["files_processed"] += 1
            bot_stats["total_users"].add(user_id)

            # Send completion message
            await message.reply_text(
                "✅ **File processing completed successfully!**\n\n"
                "🔄 **Want to rename another file?** Just send it!",
                parse_mode=enums.ParseMode.MARKDOWN
            )

        # Cleanup
        cleanup_file(download_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            cleanup_file(thumbnail_path)

        # Clear session
        if user_id in user_sessions:
            del user_sessions[user_id]

    except Exception as e:
        logger.error(f"Error in rename process: {e}")
        await message.reply_text("❌ Error processing your request.")
        
        # Cleanup on error
        user_id = message.from_user.id
        if user_id in user_sessions:
            del user_sessions[user_id]

async def handle_batch_start(client: Client, message: Message):
    """Start batch renaming mode"""
    user_id = message.from_user.id
    
    user_sessions[user_id] = {
        'batch_files': [],
        'batch_mode': True,
        'timestamp': datetime.now()
    }
    
    await message.reply_text(
        "🔄 **Batch Renaming Mode Activated!**\n\n"
        "📁 **How to use:**\n"
        "1. Send multiple files one by one (max 10 files)\n"
        "2. After sending all files, type /done\n"
        "3. Enter the naming pattern with {n} for numbers\n\n"
        "**Example patterns:**\n"
        "• `document_{n}` → document_1.pdf, document_2.pdf\n"
        "• `my_photos_{n}` → my_photos_1.jpg, my_photos_2.jpg\n\n"
        "📤 **Start sending files now!**\n"
        "Type /cancel to abort.",
        parse_mode=enums.ParseMode.MARKDOWN
    )

async def handle_batch_files(client: Client, message: Message):
    """Handle files in batch mode"""
    # Implementation similar to handle_file_message but for batch
    pass

async def handle_batch_pattern(client: Client, message: Message):
    """Handle batch naming pattern"""
    # Implementation for batch processing
    pass

async def cancel_command(client: Client, message: Message):
    """Cancel the current operation"""
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await message.reply_text(
        "❌ **Operation cancelled.**\n\n"
        "You can start over by sending a file or using /batch for multiple files.",
        parse_mode=enums.ParseMode.MARKDOWN
            )
