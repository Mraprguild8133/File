from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from file_handle import download_file, upload_file
from file_rename import rename_file
import os

# Dictionary to store user state (e.g., waiting for a new file name)
user_states = {}

def register_handlers(app: Client):
    """
    Registers all the bot's command and message handlers.
    """

    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        await message.reply_text(
            "Hello! I am a file upload and rename bot.\n\n"
            "Send me a file, and I will ask you for a new name. "
            "I can handle files up to 4GB."
        )

    @app.on_message(filters.document | filters.video | filters.audio)
    async def handle_file_message(client, message: Message):
        """
        Handles incoming files.
        """
        # Store the message ID of the file to rename it later
        user_id = message.from_user.id
        user_states[user_id] = {"file_message_id": message.id}

        await message.reply_text(
            "File received. Please send me the new name for this file (without the extension)."
        )

    @app.on_message(filters.text & filters.private)
    async def handle_text_message(client, message: Message):
        """
        Handles text messages, primarily for receiving the new file name.
        """
        user_id = message.from_user.id
        state = user_states.get(user_id)

        # Check if we are waiting for a file name from this user
        if state and "file_message_id" in state:
            file_message_id = state["file_message_id"]
            new_name = message.text.strip()

            # Get the original file message
            original_message = await client.get_messages(message.chat.id, file_message_id)

            if not original_message or not (original_message.document or original_message.video or original_message.audio):
                await message.reply_text("Could not find the original file. Please send it again.")
                user_states.pop(user_id, None)
                return

            status_msg = await message.reply_text("Processing your request...")

            # 1. Download the file
            downloaded_path = await download_file(original_message, status_msg)
            if not downloaded_path:
                user_states.pop(user_id, None)
                return

            # 2. Rename the file
            renamed_path = await rename_file(downloaded_path, new_name)
            if not renamed_path:
                await status_msg.edit_text("Failed to rename the file.")
                os.remove(downloaded_path) # Clean up
                user_states.pop(user_id, None)
                return

            # 3. Upload the renamed file
            file_caption = f"Renamed to: `{os.path.basename(renamed_path)}`"
            await upload_file(client, message.chat.id, renamed_path, status_msg, caption=file_caption)

            # 4. Forward to log channel
            await client.forward_messages(
                chat_id=Config.LOG_CHANNEL,
                from_chat_id=message.chat.id,
                message_ids=original_message.id
            )

            # 5. Clean up local files and state
            os.remove(renamed_path)
            user_states.pop(user_id, None)
        else:
            await message.reply_text("Please send me a file first before sending a name.")
