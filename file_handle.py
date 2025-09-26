import time
from pyrogram.types import Message

async def download_file(message: Message, status_message: Message):
    """
    Downloads a file from a Telegram message with a progress bar.

    Args:
        message (Message): The message containing the file to download.
        status_message (Message): The message to edit with progress updates.

    Returns:
        str: The path to the downloaded file, or None if download fails.
    """
    start_time = time.time()
    try:
        # The actual file to download (can be document, video, etc.)
        file_to_download = message.document or message.video or message.audio

        if not file_to_download:
            await status_message.edit_text("No downloadable file found in this message.")
            return None

        # Download the file
        file_path = await message.download(
            progress=_progress_callback,
            progress_args=(status_message, start_time, "Downloading")
        )
        return file_path
    except Exception as e:
        await status_message.edit_text(f"An error occurred during download: {e}")
        print(f"Download error: {e}")
        return None

async def upload_file(client, chat_id, file_path, status_message: Message, caption=""):
    """
    Uploads a file to a Telegram chat with a progress bar.

    Args:
        client: The Pyrogram client instance.
        chat_id: The ID of the chat to upload the file to.
        file_path (str): The path of the file to upload.
        status_message (Message): The message to edit with progress updates.
        caption (str): The caption for the uploaded file.
    """
    start_time = time.time()
    try:
        await client.send_document(
            chat_id=chat_id,
            document=file_path,
            caption=caption,
            progress=_progress_callback,
            progress_args=(status_message, start_time, "Uploading")
        )
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"An error occurred during upload: {e}")
        print(f"Upload error: {e}")

async def _progress_callback(current, total, status_message: Message, start_time, action):
    """
    Generic progress callback function for downloads and uploads.
    """
    elapsed_time = time.time() - start_time
    if elapsed_time == 0:
        elapsed_time = 1 # Avoid division by zero

    speed = current / elapsed_time
    percentage = (current / total) * 100
    progress_str = (
        f"{action}...\n"
        f"[{'█' * int(percentage / 5)}{' ' * (20 - int(percentage / 5))}]\n"
        f"{percentage:.2f}%\n"
        f"{_format_bytes(current)} of {_format_bytes(total)}\n"
        f"Speed: {_format_bytes(speed)}/s\n"
        f"Elapsed: {int(elapsed_time)}s"
    )
    try:
        # Edit the message only if the content has changed
        if status_message.text != progress_str:
            await status_message.edit_text(progress_str)
    except Exception:
        # Ignore errors if the message can't be edited (e.g., deleted)
        pass

def _format_bytes(size):
    """Formats file size in a human-readable format."""
    if size is None:
        return "0B"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power and n < len(power_labels) -1 :
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"
