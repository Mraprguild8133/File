from pyrogram import Client
from config import Config
from bot_handle import register_handlers

def main():
    """
    The main function to start the bot.
    """
    # Initialize the Pyrogram Client
    # Using in-memory storage for sessions for simplicity
    app = Client(
        "file_renamer_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        workers=20  # Number of concurrent workers for handling updates
    )

    # Register all the handlers for the bot
    register_handlers(app)

    # Run the bot
    print("Bot is starting...")
    app.run()
    print("Bot has stopped.")

if __name__ == "__main__":
    main()
