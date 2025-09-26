# =====================================================================================
# Project: Telegram File Rename Bot
# Description: A bot to rename Telegram files with custom thumbnail and caption support.
# Version: 2.1 (Multi-File, No Database)
# Last Updated: 26-Sep-2025
# =====================================================================================

import os
import time
import re
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Third-party libraries
try:
    from pyrogram import Client, filters
    from pyrogram.types import (
        Message,
        CallbackQuery,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )
    from pyrogram.errors import FloodWait, UserNotParticipant
except ImportError:
    print("Pyrogram is not installed. Please install it using: pip install pyrogram TgCrypto")
    exit()

# Local import from config.py
try:
    from config import Config
except ImportError:
    print("Error: config.py not found. Please ensure it's in the same directory.")
    exit()

# --- Text Messages ---
class Txt(object):
    START_MSG = """<b> Hᴇʟʟᴏ {} 👋,</b>
I ᴀᴍ ᴀɴ Aᴅᴠᴀɴᴄᴇᴅ Fɪʟᴇ Rᴇɴᴀᴍᴇʀ ᴀɴᴅ Cᴏɴᴠᴇʀᴛᴇʀ Bᴏᴛ Wɪᴛʜ Cᴜsᴛᴏᴍ Tʜᴜᴍʙɴᴀɪʟ & Cᴀᴘᴛɪᴏn Sᴜᴘᴘᴏʀᴛ.

<b>Sᴇɴᴅ Mᴇ Aɴʏ Vɪᴅᴇᴏ Oʀ Fɪʟᴇ Tᴏ Gᴇᴛ Sᴛᴀʀᴛᴇᴅ</b>.
"""
    ABOUT_MSG = """<b>Mʏ Nᴀᴍᴇ :</b> <a href='https://t.me/An_Advanced_File_Renamer_Bot'><b>Fɪʟᴇ Rᴇɴᴀᴍᴇʀ Bᴏᴛ</b></a>
<b>Cʀᴇᴀᴛᴏʀ :</b> <a href='https://t.me/No_OnE_Kn0wS_Me'><b>Nᴏ OɴE Kɴ0wS Mᴇ</b></a>
<b>Lɪʙʀᴀʀʏ :</b> <a href='https://docs.pyrogram.org'><b>Pʏʀᴏɢʀᴀᴍ</b></a>
<b>Lᴀɴɢᴜᴀɢᴇ :</b> <a href='https://www.python.org'><b>Pʏᴛʜᴏɴ 3</b></a>
<b>Sᴏᴜʀᴄᴇ :</b> <a href='https://github.com/No-OnE-Kn0wS-Me/FileRenameBot'><b>Gɪᴛʜᴜʙ</b></a>
"""
    HELP_MSG = """<b>Hᴏᴡ Tᴏ Usᴇ Mᴇ...?</b>
    
<b>➻</b> Sᴇɴᴅ Mᴇ Aɴʏ Fɪʟᴇ Oʀ Vɪᴅᴇᴏ.
<b>➻</b> Cʟɪᴄᴋ Oɴ Rᴇɴᴀᴍᴇ Bᴜᴛᴛᴏɴ.
<b>➻</b> Eɴᴛᴇʀ Nᴇᴡ Fɪʟᴇ Nᴀᴍᴇ.
<b>➻</b> I Wɪʟʟ Uᴘʟᴏᴀᴅ Yᴏᴜʀ Fɪʟᴇ Wɪᴛʜ Yᴏᴜʀ Gɪᴠᴇɴ Nᴀᴍᴇ.

<b>Hᴏᴡ Tᴏ Aᴅᴅ Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ...?</b>
<b>➻</b> Usᴇ `/set_caption` Tᴏ Sᴇᴛ Cᴀᴘᴛɪᴏɴ.
<b>➻</b> Usᴇ `/del_caption` Tᴏ Dᴇʟᴇᴛᴇ Cᴀᴘᴛɪᴏɴ.
<b>➻</b> Usᴇ `/see_caption` Tᴏ Sᴇᴇ Cᴀᴘᴛɪᴏɴ.

<b>Hᴏᴡ Tᴏ Sᴇᴛ Tʜᴜᴍʙɴᴀɪʟ...?</b>
<b>➻</b> Sᴇɴᴅ A Pʜᴏᴛᴏ Tᴏ Mᴇ Tᴏ Sᴇᴛ ɪᴛ.
<b>➻</b> Usᴇ `/del_thumb` Tᴏ Dᴇʟᴇᴛᴇ Tʜᴜᴍʙɴᴀɪʟ.
<b>➻</b> Usᴇ `/see_thumb` Tᴏ Sᴇᴇ Tʜᴜᴍʙɴᴀɪʟ.
"""
    PROGRESS_BAR = "<b>Sɪᴢᴇ : {1} | {2}\nDᴏɴᴇ : {0}%\nSᴘᴇᴇᴅ : {3}/s\nEᴛᴀ : {4}</b>"

# --- In-Memory Data Storage ---
user_data = {}

class InMemoryDatabase:
    def __init__(self, user_id):
        self.id = user_id

    def _get_or_create_user(self, name=None):
        if self.id not in user_data:
            user_data[self.id] = {'caption': None, 'thumbnail': None}
        return user_data[self.id]

    async def get_user(self):
        return self._get_or_create_user()

    async def set_caption(self, caption):
        self._get_or_create_user()['caption'] = caption

    async def set_thumbnail(self, thumbnail):
        self._get_or_create_user()['thumbnail'] = thumbnail

    async def delete_thumbnail(self):
        if self.id in user_data: user_data[self.id]['thumbnail'] = None

    async def delete_caption(self):
        if self.id in user_data: user_data[self.id]['caption'] = None

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[RotatingFileHandler("bot.log", maxBytes=5000000, backupCount=10), logging.StreamHandler()])
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

# --- Bot Initialization ---
bot = Client("FileRenameBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# --- Helper Functions ---
def humanbytes(size):
    if not size: return "0 B"
    power, n = 1024, 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {power_labels[n]}B"

def TimeFormatter(milliseconds: int) -> str:
    secs, Mins, hrs, days = (milliseconds / 1000), 0, 0, 0
    if secs >= 60: Mins, secs = divmod(secs, 60)
    if Mins >= 60: hrs, Mins = divmod(Mins, 60)
    if hrs >= 24: days, hrs = divmod(hrs, 24)
    return f"{str(int(days)) + 'd ' if days > 0 else ''}{str(int(hrs)) + 'h ' if hrs > 0 else ''}{str(int(Mins)) + 'm ' if Mins > 0 else ''}{str(int(secs)) + 's' if secs > 0 else ''}"

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        eta = TimeFormatter(round((total - current) / speed) * 1000) if speed > 0 else 'N/A'
        progress_str = Txt.PROGRESS_BAR.format(round(percentage, 2), humanbytes(current), humanbytes(total), humanbytes(speed), eta)
        try: await message.edit(text=f"**{ud_type}**\n\n{progress_str}")
        except (FloodWait, ConnectionError): pass

# --- Command & Message Handlers ---
@bot.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton('Uᴘᴅᴀᴛᴇs', url='https://t.me/Mo_Tech_YT'), InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ', url='https://t.me/Mo_Tech_Group')],
        [InlineKeyboardButton('Aʙᴏᴜᴛ', callback_data='about'), InlineKeyboardButton('Hᴇʟᴘ', callback_data='help')]
    ])
    caption = Txt.START_MSG.format(message.from_user.mention)
    if Config.START_PIC: await message.reply_photo(Config.START_PIC, caption=caption, reply_markup=buttons)
    else: await message.reply_text(text=caption, reply_markup=buttons, disable_web_page_preview=True)

@bot.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def file_handler(client, message: Message):
    file = message.document or message.video or message.audio
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📝 Rename", callback_data="rename"), InlineKeyboardButton("✖️ Cancel", callback_data="close")]])
    await message.reply_text(f"**File Name:** `{file.file_name}`\n**File Size:** `{humanbytes(file.file_size)}`\n\nSelect an option:", reply_markup=buttons, quote=True)

@bot.on_message(filters.private & filters.photo)
async def set_thumbnail_command(client, message):
    await InMemoryDatabase(message.from_user.id).set_thumbnail(message.photo.file_id)
    await message.reply_text("✅ Your custom thumbnail has been saved.", quote=True)

# --- Callback Query Handler ---
@bot.on_callback_query()
async def callback_query_handler(client, query: CallbackQuery):
    data = query.data
    message = query.message
    
    if data == "rename":
        await message.delete()
        try:
            ask = await client.ask(query.from_user.id, "**Send me the new filename.**\n\n_Include the file extension._", timeout=300)
            await process_rename(client, message.reply_to_message, ask.text)
        except asyncio.TimeoutError:
            await client.send_message(query.from_user.id, "⚠️ **Timeout:** Task cancelled.")
        except Exception as e:
            LOGGER.error(e)
            await message.reply_text("An error occurred. Please try again.")
            
    elif data == "close": await message.delete()
    elif data == "help": await message.edit_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="start")]]))
    elif data == "about": await message.edit_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="start")]]))
    elif data == "start":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton('Uᴘᴅᴀᴛᴇs', url='https://t.me/Mo_Tech_YT'), InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ', url='https://t.me/Mo_Tech_Group')],
            [InlineKeyboardButton('Aʙᴏᴜᴛ', callback_data='about'), InlineKeyboardButton('Hᴇʟᴘ', callback_data='help')]
        ])
        await message.edit_reply_markup(buttons)

async def process_rename(client, message, new_name: str):
    if Config.FORCE_SUB:
        try:
            if not await client.get_chat_member(Config.FORCE_SUB, message.from_user.id):
                return await message.reply_text(f"**You must join our channel to use this bot.**\n\n👉 https://t.me/{Config.FORCE_SUB}")
        except UserNotParticipant:
            return await message.reply_text(f"**You must join our channel to use this bot.**\n\n👉 https://t.me/{Config.FORCE_SUB}")

    user_info = await InMemoryDatabase(message.from_user.id).get_user()
    file = message.document or message.video or message.audio
    
    status_msg = await message.reply_text("📥 Downloading...", quote=True)
    
    file_path, thumb_path = None, None
    try:
        file_path = await message.download(progress=progress_for_pyrogram, progress_args=("Downloading...", status_msg, time.time()))
        if user_info.get('thumbnail'):
            thumb_path = await client.download_media(user_info['thumbnail'])
    except Exception as e:
        return await status_msg.edit(f"❌ **Download Failed:** {e}")

    new_file_path = os.path.join(os.path.dirname(file_path), new_name)
    os.rename(file_path, new_file_path)

    await status_msg.edit("📤 Uploading...")
    
    caption = user_info.get('caption', new_name).format(filename=new_name, filesize=humanbytes(file.file_size))
    
    try:
        send_func = getattr(client, f"send_{message.media.value}")
        await send_func(
            message.chat.id, document=new_file_path if message.document else new_file_path,
            thumb=thumb_path, caption=caption,
            progress=progress_for_pyrogram, progress_args=("Uploading...", status_msg, time.time())
        )
        if Config.LOG_CHANNEL:
            await client.send_message(Config.LOG_CHANNEL, f"**User:** {message.from_user.mention}\n**Renamed:** `{file.file_name}` -> `{new_name}`")
    except Exception as e:
        await status_msg.edit(f"❌ **Upload Failed:** {e}")
    finally:
        await status_msg.delete()
        if file_path and os.path.exists(file_path): os.remove(file_path)
        if new_file_path and os.path.exists(new_file_path): os.remove(new_file_path)
        if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)

# --- Main Execution ---
if __name__ == "__main__":
    if not all([Config.API_ID, Config.API_HASH, Config.BOT_TOKEN, Config.ADMIN, Config.LOG_CHANNEL]):
        LOGGER.critical("FATAL ERROR: One or more required variables in config.py are missing!")
        exit(1)
    LOGGER.info("Bot is starting...")
    bot.run()
    LOGGER.info("Bot has stopped.")
