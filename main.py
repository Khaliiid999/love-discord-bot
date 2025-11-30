import os
import disnake
from disnake.ext import commands
import sqlite3

# If you still have economy features and the folder, keep this import.
# If not, delete this line.
from economy.economy import Economy  

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(command_prefix="l!", intents=intents)
bot.channel_conversations = {}


def setup_database():
    """Initialize the SQLite database for user memory."""
    bot.conn = sqlite3.connect("user_memory.db")
    bot.cursor = bot.conn.cursor()
    bot.cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_memory (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            info TEXT
        )
        """
    )
    bot.conn.commit()


bot.setup_database = setup_database
bot.setup_database()

# Attach economy if present
try:
    bot.economy = Economy()
except Exception as e:
    print(f"Economy init failed (you can remove this if unused): {e}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(
        status=disnake.Status.idle,
        activity=disnake.Activity(
            type=disnake.ActivityType.playing,
            name="with Love",
        ),
    )


files = {
    "fun": [
        "cat",
        "coin_flip",
        "dice",
        "greetings",
        "joke",
        "match",
    ],
    "ai": [
        "text-gen",
    ],
    "events": [
        "welcome",
    ],
    "economy": [
        "balance",
        "daily",
        "leaderboard",
        "message_listener",
        "gambling",
        "pay",
    ],
    "moderation": [
        "ban",
        "clear",
        "kick",
        "mute",
        "clone",
        "verify",
        "reactrole",
    ],
}  # ← only this one closing brace for the dict

for folder in files:
    for file in files[folder]:
        try:
            bot.load_extension(f"{folder}.{file}")
            print(f"Loaded cog {folder}.{file}")
        except Exception as e:
            print(f"Failed to load cog {folder}.{file}: {e}")

if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    if not token:
        raise RuntimeError("Set your Discord bot token in the TOKEN environment variable.")
    bot.run(token)
