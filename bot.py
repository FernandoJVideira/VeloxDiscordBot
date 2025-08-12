import os
import sys
from dotenv import load_dotenv
from cogs.DatabaseHandler import DatabaseHandler
import discord
from discord.ext import commands
from cogs.constants import EXTENTIONS

class VeloxBot(commands.Bot):
    def __init__(self):
        # Load environment variables first
        load_dotenv("./vars.env")

        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=os.getenv("APPLICATION_ID"))

        # Initialize database
        try:
            self.db = DatabaseHandler()
            self.db.createDatabase()
            print("✅ Database connection established successfully")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            print("Make sure PostgreSQL is running and environment variables are set correctly")
            sys.exit(1)

    async def setup_hook(self):
        print("🔧 Loading extensions...")
        for extension in EXTENTIONS:
            try:
                await self.load_extension(extension)
                print(f"✅ Loaded {extension}")
            except Exception as e:
                print(f"❌ Failed to load {extension}: {e}")

    async def on_ready(self):
        print(f"🤖 {self.user} is ready and connected to PostgreSQL!")
        print(f"📊 Serving {len(self.guilds)} guilds")

    async def close(self):
        print("🔄 Shutting down bot and closing database connections...")
        if hasattr(self, 'db'):
            self.db.close_pool()
        await super().close()

def main():
    bot = VeloxBot()
    load_dotenv("./vars.env")
    token = os.getenv("TOKEN")
    if not token:
        print("❌ Discord bot token not found in environment variables!")
        print("Make sure TOKEN is set in your vars.env file")
        sys.exit(1)
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
