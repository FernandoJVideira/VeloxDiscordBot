import os
import sys
import logging
#from dotenv import load_dotenv
from cogs.DatabaseHandler import DatabaseHandler
import discord
from discord.ext import commands
from cogs.constants import EXTENTIONS

# Set up logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

class VeloxBot(commands.Bot):
    def __init__(self):
        # Load environment variables first
        #load_dotenv("./vars.env")

        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=os.getenv("APPLICATION_ID"))

        # Initialize database
        try:
            self.db = DatabaseHandler()
            self.db.createDatabase()
            logging.info("✅ Database connection established successfully")
        except Exception as e:
            logging.error(f"❌ Failed to connect to database: {e}")
            sys.exit(1)

    async def setup_hook(self):
        logging.info("🔧 Loading extensions...")
        for extension in EXTENTIONS:
            try:
                await self.load_extension(extension)
                logging.info(f"✅ Loaded {extension}")
            except Exception as e:
                logging.error(f"❌ Failed to load {extension}: {e}")

    async def on_ready(self):
        logging.info(f"🤖 {self.user} is ready and connected to PostgreSQL!")
        logging.info(f"📊 Serving {len(self.guilds)} guilds")

    async def close(self):
        logging.info("🔄 Shutting down bot and closing database connections...")
        if hasattr(self, 'db'):
            self.db.close_pool()
        await super().close()

def main():
    bot = VeloxBot()
    token = os.getenv("TOKEN")
    if not token:
        logging.error("❌ Discord bot token not found in environment variables!")
        logging.error("Make sure TOKEN is set in your vars.env file")
        sys.exit(1)
    try:
        bot.run(token)
    except Exception as e:
        logging.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
