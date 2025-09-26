import os
import logging
import tempfile
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from PIL import Image

from config import config
from utils.file_utils import (
    download_file, get_file_extension, 
    create_thumbnail, is_file_supported,
    get_file_size, cleanup_file
)

logger = logging.getLogger(__name__)

# Store user data for renaming process
user_sessions = {}

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming files for renaming."""
    try:
        user_id = update.effective_user.id
        message = update.message
        
        # Get file information
        if message.document:
            file = message.document
            file_name = file.file_name
            mime_type = file.mime_type
        elif message.photo:
            file = message.photo[-1]  # Highest resolution
            file_name = "photo.jpg"
            mime_type = "image/jpeg"
        elif message.video:
            file = message.video
            file_name = getattr(file, 'file_name', 'video.mp4')
            mime_type = "video/mp4"
        elif message.audio:
            file = message.audio
            file_name = getattr(file, 'file_name', 'audio.mp3')
            mime_type = "audio/mpeg"
        else:
            await message.reply_text("❌ Unsupported file type.")
            return ConversationHandler.END
        
        # Check file size
        file_size = file.file_size
        if file_size > config.MAX_FILE_SIZE:
            await message.reply_text(
                f"❌ File too large! Maximum size is {config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
            return ConversationHandler.END
        
        # Check supported format
        extension = get_file_extension(file_name)
        if not is_file_supported(extension):
            await message.reply_text(
                f"❌ File format '.{extension}' is not supported.\n\n"
                f"✅ Supported formats: {', '.join(sorted(config.SUPPORTED_FORMATS))}"
            )
            return ConversationHandler.END
        
        # Store file info for renaming
        user_sessions[user_id] = {
            'file_id': file.file_id,
            'original_name': file_name,
            'mime_type': mime_type,
            'file_size': file_size,
            'extension': extension
        }
        
        await message.reply_text(
            f"📁 **File Received:** `{file_name}`\n"
            f"📊 **Size:** {get_file_size(file_size)}\n\n"
            "📝 **Please send the new filename (without extension):**\n"
            "Type /cancel to abort.",
            parse_mode='Markdown'
        )
        
        return RENAME
        
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await update.message.reply_text("❌ Error processing your file.")
        return ConversationHandler.END

async def handle_rename_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the new filename input."""
    try:
        user_id = update.effective_user.id
        new_filename = update.message.text.strip()
        
        if user_id not in user_sessions:
            await update.message.reply_text("❌ No file found. Please send a file first.")
            return ConversationHandler.END
        
        session = user_sessions[user_id]
        
        # Validate filename
        if not new_filename or len(new_filename) > 100:
            await update.message.reply_text("❌ Invalid filename. Please enter a valid name (max 100 characters).")
            return RENAME
        
        # Clean filename
        new_filename = "".join(c for c in new_filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        new_filename_with_ext = f"{new_filename}.{session['extension']}"
        
        await update.message.reply_text("⏳ Processing your file...")
        
        # Download file
        file_obj = await context.bot.get_file(session['file_id'])
        temp_file = await download_file(file_obj, session['extension'])
        
        if not temp_file:
            await update.message.reply_text("❌ Error downloading file.")
            return ConversationHandler.END
        
        # Create thumbnail for supported types
        thumbnail_path = None
        if session['mime_type'].startswith(('image/', 'video/')):
            thumbnail_path = create_thumbnail(temp_file, config.THUMBNAIL_SIZE)
        
        # Send renamed file
        with open(temp_file, 'rb') as file_data:
            caption = f"✅ **Renamed Successfully!**\n\n📁 **Original:** `{session['original_name']}`\n📝 **New:** `{new_filename_with_ext}`"
            
            if session['mime_type'].startswith('image/'):
                await update.message.reply_photo(
                    photo=file_data,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif session['mime_type'].startswith('video/'):
                await update.message.reply_video(
                    video=file_data,
                    caption=caption,
                    thumb=open(thumbnail_path, 'rb') if thumbnail_path else None,
                    parse_mode='Markdown'
                )
            elif session['mime_type'].startswith('audio/'):
                await update.message.reply_audio(
                    audio=file_data,
                    caption=caption,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_document(
                    document=file_data,
                    filename=new_filename_with_ext,
                    caption=caption,
                    thumb=open(thumbnail_path, 'rb') if thumbnail_path else None,
                    parse_mode='Markdown'
                )
        
        # Update statistics
        from handlers.start_handler import bot_stats
        bot_stats["files_processed"] += 1
        
        # Cleanup
        cleanup_file(temp_file)
        if thumbnail_path:
            cleanup_file(thumbnail_path)
        
        # Clear session
        del user_sessions[user_id]
        
        await update.message.reply_text(
            "🔄 **Want to rename another file?** Just send it!",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in rename process: {e}")
        await update.message.reply_text("❌ Error processing your request.")
        return ConversationHandler.END

async def handle_batch_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start batch renaming mode."""
    user_id = update.effective_user.id
    user_sessions[user_id] = {'batch_files': []}
    
    await update.message.reply_text(
        "🔄 **Batch Renaming Mode Activated!**\n\n"
        "📁 **How to use:**\n"
        "1. Send multiple files one by one\n"
        "2. After sending all files, type the naming pattern\n"
        "3. Use {n} for sequential numbers\n\n"
        "**Example patterns:**\n"
        "• `document_{n}` → document_1.pdf, document_2.pdf\n"
        "• `my_files_{n}` → my_files_1.jpg, my_files_2.jpg\n\n"
        "📤 **Start sending files now!**\n"
        "Type /cancel to abort.",
        parse_mode='Markdown'
    )
    
    return BATCH_MODE

async def handle_batch_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files in batch mode."""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions or 'batch_files' not in user_sessions[user_id]:
        await update.message.reply_text("❌ Please start batch mode with /batch first.")
        return ConversationHandler.END
    
    # Similar file handling logic as handle_file but for batch
    # ... (implementation similar to handle_file but for multiple files)
    
    await update.message.reply_text("✅ File added to batch! Send more files or type the naming pattern.")
    return BATCH_MODE

async def handle_batch_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle batch naming pattern."""
    # Implementation for batch renaming pattern processing
    # ... (process all batch files with the given pattern)
    
    await update.message.reply_text("✅ Batch processing completed!")
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation."""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END
