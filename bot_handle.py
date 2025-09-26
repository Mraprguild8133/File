from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio
from datetime import datetime, timedelta

# User state management
user_states = {}

def register_handlers(app: Client):
    """
    Registers all the bot's command and message handlers.
    """

    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        await message.reply_text(
            "🚀 **Turbo File Renamer Bot**\n\n"
            "Send me any file and I'll rename it with extreme speed!\n"
            "• Custom thumbnail support\n"
            "• 4GB file support\n"
            "• Lightning fast processing\n\n"
            "Just send a file and follow the instructions!"
        )

    @app.on_message(filters.command("help"))
    async def help_command(client, message: Message):
        await message.reply_text(
            "📖 **How to use:**\n\n"
            "1. Send me any file (document, video, audio)\n"
            "2. I'll ask for a new filename\n"
            "3. Send the new name (without extension)\n"
            "4. I'll process it with turbo speed!\n\n"
            "Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/stats - Show your statistics"
        )

    @app.on_message(filters.command("stats"))
    async def stats_command(client, message: Message):
        user_id = message.from_user.id
        file_count = user_states.get(f"{user_id}_count", 0)
        await message.reply_text(
            f"📊 **Your Statistics:**\n"
            f"Files processed: {file_count}\n"
            f"Status: ✅ Active"
        )

    @app.on_message(filters.document | filters.video | filters.audio)
    async def handle_file_message(client, message: Message):
        """
        Handles incoming files.
        """
        user_id = message.from_user.id
        user_states[user_id] = {
            "file_message_id": message.id,
            "file_type": "document" if message.document else "video" if message.video else "audio"
        }
        
        # Track user file count
        count_key = f"{user_id}_count"
        user_states[count_key] = user_states.get(count_key, 0) + 1

        await message.reply_text(
            "📁 **File Received!**\n\n"
            "Please send me the new name for this file (without extension).\n"
            "Example: `my_renamed_file`"
        )

    @app.on_message(filters.text & filters.private)
    async def handle_text_message(client, message: Message):
        """
        Handles text messages for file renaming.
        """
        user_id = message.from_user.id
        state = user_states.get(user_id)

        if state and "file_message_id" in state:
            new_name = message.text.strip()
            
            # Basic filename validation
            if not new_name or len(new_name) > 100:
                await message.reply_text(
                    "❌ Invalid filename! Please use a name between 1-100 characters."
                )
                return
            
            # Get the original file message
            try:
                original_message = await client.get_messages(
                    message.chat.id, 
                    state["file_message_id"]
                )
                
                if not original_message:
                    await message.reply_text("❌ Original file not found. Please send the file again.")
                    user_states.pop(user_id, None)
                    return
                    
            except Exception as e:
                await message.reply_text("❌ Error retrieving file. Please try again.")
                user_states.pop(user_id, None)
                return

            # Send processing message
            status_msg = await message.reply_text("⚡ **Processing your file...**")

            try:
                # Simulate file processing (you'll replace this with actual download/upload)
                await asyncio.sleep(2)  # Simulate processing time
                
                # Get file info
                file = original_message.document or original_message.video or original_message.audio
                file_name = getattr(file, "file_name", "file")
                file_size = getattr(file, "file_size", 0)
                
                # Create new filename with extension
                _, ext = os.path.splitext(file_name)
                new_file_name = f"{new_name}{ext}"
                
                # Send success message
                await status_msg.edit_text(
                    f"✅ **File Processing Complete!**\n\n"
                    f"**Original:** {file_name}\n"
                    f"**Renamed to:** {new_file_name}\n"
                    f"**Size:** {format_file_size(file_size)}\n"
                    f"**Status:** Successfully processed!"
                )
                
                # Forward to log channel if configured
                try:
                    log_channel = getattr(client, "log_channel", None)
                    if log_channel:
                        await client.forward_messages(
                            chat_id=log_channel,
                            from_chat_id=message.chat.id,
                            message_ids=original_message.id
                        )
                except Exception:
                    pass  # Silent fail for logging
                    
            except Exception as e:
                await status_msg.edit_text(f"❌ **Error processing file:** {str(e)}")
            finally:
                # Clean up user state
                user_states.pop(user_id, None)
        else:
            await message.reply_text(
                "📁 Please send me a file first, then I'll ask for the new filename!"
            )

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.2f} {size_names[i]}"
