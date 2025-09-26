import os
import logging
import tempfile
from datetime import datetime
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

# Conversation states (should match bot.py)
RENAME, BATCH_MODE, BROADCAST = range(3)

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
            'extension': extension,
            'timestamp': datetime.now()
        }
        
        await message.reply_text(
            f"📁 **File Received:** `{file_name}`\n"
            f"📊 **Size:** {get_file_size(file_size)}\n"
            f"🔤 **Format:** {extension.upper()}\n\n"
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
        
        # Clean filename (remove invalid characters)
        import re
        new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename)  # Remove invalid filename characters
        new_filename = new_filename.strip()
        
        if not new_filename:
            await update.message.reply_text("❌ Please provide a valid filename.")
            return RENAME
        
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
            caption = (
                f"✅ **Renamed Successfully!**\n\n"
                f"📁 **Original:** `{session['original_name']}`\n"
                f"📝 **New:** `{new_filename_with_ext}`\n"
                f"📊 **Size:** {get_file_size(session['file_size'])}\n"
                f"⏰ **Processed in:** {(datetime.now() - session['timestamp']).total_seconds():.1f}s"
            )
            
            if session['mime_type'].startswith('image/'):
                await update.message.reply_photo(
                    photo=file_data,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif session['mime_type'].startswith('video/'):
                thumb_file = open(thumbnail_path, 'rb') if thumbnail_path and os.path.exists(thumbnail_path) else None
                await update.message.reply_video(
                    video=file_data,
                    caption=caption,
                    thumb=thumb_file,
                    parse_mode='Markdown'
                )
                if thumb_file:
                    thumb_file.close()
            elif session['mime_type'].startswith('audio/'):
                await update.message.reply_audio(
                    audio=file_data,
                    caption=caption,
                    parse_mode='Markdown'
                )
            else:
                thumb_file = open(thumbnail_path, 'rb') if thumbnail_path and os.path.exists(thumbnail_path) else None
                await update.message.reply_document(
                    document=file_data,
                    filename=new_filename_with_ext,
                    caption=caption,
                    thumb=thumb_file,
                    parse_mode='Markdown'
                )
                if thumb_file:
                    thumb_file.close()
        
        # Update statistics
        from handlers.start_handler import bot_stats
        bot_stats["files_processed"] += 1
        
        # Cleanup
        cleanup_file(temp_file)
        if thumbnail_path and os.path.exists(thumbnail_path):
            cleanup_file(thumbnail_path)
        
        # Clear session
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        # Send completion message with buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("🔄 Rename Another File", callback_data="rename_help")],
            [InlineKeyboardButton("📊 Bot Status", callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ **File processing completed!**\n\n"
            "🔄 **Want to rename another file?** Just send it!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in rename process: {e}")
        await update.message.reply_text("❌ Error processing your request.")
        
        # Cleanup on error
        user_id = update.effective_user.id
        if user_id in user_sessions:
            del user_sessions[user_id]
            
        return ConversationHandler.END

async def handle_batch_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start batch renaming mode."""
    user_id = update.effective_user.id
    
    # Initialize batch session
    user_sessions[user_id] = {
        'batch_files': [],
        'batch_mode': True,
        'timestamp': datetime.now()
    }
    
    await update.message.reply_text(
        "🔄 **Batch Renaming Mode Activated!**\n\n"
        "📁 **How to use:**\n"
        "1. Send multiple files one by one (max 10 files)\n"
        "2. After sending all files, type /done\n"
        "3. Enter the naming pattern with {n} for numbers\n\n"
        "**Example patterns:**\n"
        "• `document_{n}` → document_1.pdf, document_2.pdf\n"
        "• `my_photos_{n}` → my_photos_1.jpg, my_photos_2.jpg\n"
        "• `files_{n}` → files_1.zip, files_2.txt\n\n"
        "📤 **Start sending files now!**\n"
        "Type /cancel to abort or /done when finished.",
        parse_mode='Markdown'
    )
    
    return BATCH_MODE

async def handle_batch_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files in batch mode."""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_sessions or not user_sessions[user_id].get('batch_mode'):
            await update.message.reply_text("❌ Please start batch mode with /batch first.")
            return ConversationHandler.END
        
        message = update.message
        session = user_sessions[user_id]
        
        # Get file information (similar to handle_file)
        if message.document:
            file = message.document
            file_name = file.file_name
            mime_type = file.mime_type
        elif message.photo:
            file = message.photo[-1]
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
            return BATCH_MODE
        
        # Check file size and format
        file_size = file.file_size
        if file_size > config.MAX_FILE_SIZE:
            await message.reply_text(f"❌ File too large! Maximum size is {config.MAX_FILE_SIZE // (1024*1024)}MB")
            return BATCH_MODE
        
        extension = get_file_extension(file_name)
        if not is_file_supported(extension):
            await message.reply_text(f"❌ File format '.{extension}' is not supported.")
            return BATCH_MODE
        
        # Check batch limit
        if len(session['batch_files']) >= 10:
            await message.reply_text("❌ Batch limit reached (10 files max). Type /done to proceed.")
            return BATCH_MODE
        
        # Add file to batch
        session['batch_files'].append({
            'file_id': file.file_id,
            'original_name': file_name,
            'mime_type': mime_type,
            'file_size': file_size,
            'extension': extension
        })
        
        await update.message.reply_text(
            f"✅ **File {len(session['batch_files'])} added to batch!**\n\n"
            f"📁 **File:** `{file_name}`\n"
            f"📊 **Size:** {get_file_size(file_size)}\n"
            f"📋 **Total files:** {len(session['batch_files']}/10\n\n"
            "📤 **Send more files or type /done to proceed.**",
            parse_mode='Markdown'
        )
        
        return BATCH_MODE
        
    except Exception as e:
        logger.error(f"Error handling batch file: {e}")
        await update.message.reply_text("❌ Error processing your file.")
        return BATCH_MODE

async def handle_batch_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle batch naming pattern."""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_sessions or not user_sessions[user_id].get('batch_mode'):
            await update.message.reply_text("❌ No active batch session.")
            return ConversationHandler.END
        
        session = user_sessions[user_id]
        batch_files = session.get('batch_files', [])
        
        if not batch_files:
            await update.message.reply_text("❌ No files in batch. Please send files first.")
            return BATCH_MODE
        
        pattern = update.message.text.strip()
        
        # Validate pattern
        if not pattern or '{n}' not in pattern:
            await update.message.reply_text(
                "❌ Invalid pattern. Please include {n} for sequential numbers.\n\n"
                "**Examples:**\n"
                "• `document_{n}`\n"
                "• `my_files_{n}`\n"
                "• `photos_{n}`"
            )
            return BATCH_MODE
        
        await update.message.reply_text(f"⏳ Processing {len(batch_files)} files with pattern: `{pattern}`...")
        
        # Process each file in batch
        success_count = 0
        for i, file_info in enumerate(batch_files, 1):
            try:
                new_filename = pattern.replace('{n}', str(i))
                new_filename_with_ext = f"{new_filename}.{file_info['extension']}"
                
                # Download file
                file_obj = await context.bot.get_file(file_info['file_id'])
                temp_file = await download_file(file_obj, file_info['extension'])
                
                if temp_file:
                    # Send renamed file
                    with open(temp_file, 'rb') as file_data:
                        caption = f"📁 **Batch File {i}:** `{new_filename_with_ext}`"
                        
                        if file_info['mime_type'].startswith('image/'):
                            await update.message.reply_photo(
                                photo=file_data,
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        elif file_info['mime_type'].startswith('video/'):
                            await update.message.reply_video(
                                video=file_data,
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        elif file_info['mime_type'].startswith('audio/'):
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
                                parse_mode='Markdown'
                            )
                    
                    cleanup_file(temp_file)
                    success_count += 1
                    
                    # Small delay between files to avoid rate limiting
                    import asyncio
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing batch file {i}: {e}")
                continue
        
        # Update statistics
        from handlers.start_handler import bot_stats
        bot_stats["files_processed"] += success_count
        
        # Clear session
        del user_sessions[user_id]
        
        await update.message.reply_text(
            f"✅ **Batch processing completed!**\n\n"
            f"📊 **Results:** {success_count}/{len(batch_files)} files processed successfully\n"
            f"⏰ **Total time:** {(datetime.now() - session['timestamp']).total_seconds():.1f}s\n\n"
            f"🔄 **Start new batch with /batch**",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        await update.message.reply_text("❌ Error processing batch files.")
        
        # Cleanup on error
        user_id = update.effective_user.id
        if user_id in user_sessions:
            del user_sessions[user_id]
            
        return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation."""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text(
        "❌ **Operation cancelled.**\n\n"
        "You can start over by sending a file or using /batch for multiple files.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish file collection in batch mode and ask for pattern."""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions or not user_sessions[user_id].get('batch_mode'):
        await update.message.reply_text("❌ No active batch session.")
        return ConversationHandler.END
    
    session = user_sessions[user_id]
    batch_files = session.get('batch_files', [])
    
    if not batch_files:
        await update.message.reply_text("❌ No files in batch. Please send files first.")
        return BATCH_MODE
    
    await update.message.reply_text(
        f"✅ **Batch collection complete!**\n\n"
        f"📁 **Total files:** {len(batch_files)}\n"
        f"📊 **Total size:** {sum(f['file_size'] for f in batch_files) / (1024*1024):.1f}MB\n\n"
        "📝 **Please enter the naming pattern (use {n} for numbers):**\n\n"
        "**Examples:**\n"
        "• `document_{n}` → document_1.pdf, document_2.jpg\n"
        "• `my_photos_{n}` → my_photos_1.png, my_photos_2.png\n"
        "• `files_{n}` → files_1.zip, files_2.txt",
        parse_mode='Markdown'
    )
    
    return BATCH_MODE
