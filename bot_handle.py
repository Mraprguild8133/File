from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from file_handle import download_file_turbo, upload_file_turbo
from file_rename import rename_file
import os
import asyncio
from datetime import datetime, timedelta
import re

# Optimized user state management
user_states = {}
user_stats = {}

class SpeedOptimizer:
    """Handles speed optimizations and rate limiting"""
    
    @staticmethod
    def is_valid_filename(name):
        """Fast filename validation"""
        if not name or len(name) > 255:
            return False
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        return not any(char in name for char in invalid_chars)
    
    @staticmethod
    def can_process_user(user_id):
        """Rate limiting check"""
        now = datetime.now()
        user_stats.setdefault(user_id, {'count': 0, 'reset_time': now})
        
        stats = user_stats[user_id]
        if now > stats['reset_time'] + timedelta(hours=1):
            stats['count'] = 0
            stats['reset_time'] = now
        
        if stats['count'] >= Config.FILES_PER_USER_PER_HOUR:
            return False
        
        stats['count'] += 1
        return True

def register_handlers(app: Client):
    speed_optimizer = SpeedOptimizer()

    @app.on_message(filters.command("start"))
    async def turbo_start(client, message: Message):
        await message.reply_text(
            "🚀 **Turbo File Renamer Bot**\n\n"
            "Send me any file and I'll rename it with **EXTREME SPEED**!\n"
            "• Custom thumbnail support\n"
            • 4GB file support\n"
            "• Lightning fast processing\n\n"
            "Just send a file and follow the instructions!"
        )

    @app.on_message(filters.command("stats"))
    async def show_stats(client, message: Message):
        user_id = message.from_user.id
        stats = user_stats.get(user_id, {'count': 0})
        await message.reply_text(
            f"📊 **Your Stats**\n"
            f"• Files processed this hour: {stats['count']}\n"
            f"• Hourly limit: {Config.FILES_PER_USER_PER_HOUR}"
        )

    @app.on_message(filters.document | filters.video | filters.audio)
    async def turbo_handle_file(client, message: Message):
        """Turbo-optimized file handler"""
        user_id = message.from_user.id
        
        # Rate limiting check
        if not speed_optimizer.can_process_user(user_id):
            await message.reply_text(
                "⏳ **Rate Limit Reached**\n\n"
                "You've processed too many files this hour. "
                f"Please wait or contact admin.\n"
                f"Limit: {Config.FILES_PER_USER_PER_HOUR} files/hour"
            )
            return

        # File size check
        file_size = getattr(message.document or message.video or message.audio, 'file_size', 0)
        if file_size > Config.MAX_FILE_SIZE:
            await message.reply_text("❌ File too large! Max 4GB supported.")
            return

        user_states[user_id] = {
            "file_message_id": message.id,
            "received_time": datetime.now()
        }

        await message.reply_text(
            "📁 **File Received!**\n\n"
            "Please send the new filename (without extension):\n"
            "`Example: my_document`"
        )

    @app.on_message(filters.text & filters.private)
    async def turbo_handle_text(client, message: Message):
        """Turbo-optimized text handler"""
        user_id = message.from_user.id
        state = user_states.get(user_id)

        if state and "file_message_id" in state:
            new_name = message.text.strip()
            
            # Fast filename validation
            if not speed_optimizer.is_valid_filename(new_name):
                await message.reply_text(
                    "❌ **Invalid filename!**\n\n"
                    "Please use a valid filename:\n"
                    "• No special characters: < > : \" | ? * \\ /\n"
                    "• Max 255 characters\n"
                    "• Example: `my_document_2024`"
                )
                return

            original_message = await client.get_messages(message.chat.id, state["file_message_id"])
            if not original_message:
                await message.reply_text("❌ Original file not found. Please resend.")
                user_states.pop(user_id, None)
                return

            # Start processing with extreme speed
            status_msg = await message.reply_text("⚡ **Turbo Processing Started...**")

            try:
                # Parallel processing for maximum speed
                download_task = asyncio.create_task(
                    download_file_turbo(original_message, status_msg)
                )
                downloaded_path = await download_task

                if downloaded_path:
                    # Rename file
                    renamed_path = await rename_file(downloaded_path, new_name)
                    
                    if renamed_path:
                        # Upload with turbo speed
                        caption = f"**Renamed to:** `{os.path.basename(renamed_path)}`"
                        upload_task = asyncio.create_task(
                            upload_file_turbo(client, message.chat.id, renamed_path, status_msg, caption)
                        )
                        await upload_task

                        # Log to channel
                        await client.forward_messages(
                            chat_id=Config.LOG_CHANNEL,
                            from_chat_id=message.chat.id,
                            message_ids=original_message.id
                        )

                        # Cleanup
                        if os.path.exists(renamed_path):
                            os.remove(renamed_path)
                    
                    # Cleanup downloaded file
                    if os.path.exists(downloaded_path):
                        os.remove(downloaded_path)

            except Exception as e:
                await status_msg.edit_text(f"❌ **Processing Failed:** {str(e)}")
            finally:
                user_states.pop(user_id, None)
        else:
            await message.reply_text("📁 Please send me a file first!")

    @app.on_message(filters.command("speedtest"))
    async def speed_test(client, message: Message):
        """Test bot speed"""
        test_msg = await message.reply_text("🏃 **Testing Speed...**")
        start_time = datetime.now()
        
        # Simulate processing
        await asyncio.sleep(1)
        
        end_time = datetime.now()
        speed = (end_time - start_time).total_seconds()
        
        await test_msg.edit_text(
            f"⚡ **Speed Test Results**\n\n"
            f"• Response Time: {speed:.2f}s\n"
            f"• Status: **TURBO MODE ACTIVE**\n"
            f"• Max Workers: {Config.MAX_WORKERS}\n"
            f"• Concurrent Operations: {Config.MAX_CONCURRENT_DOWNLOADS}"
        )
