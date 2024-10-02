import os
#from dotenv import load_dotenv   # Uncomment this line for local development
from cogs.DatabaseHandler import DatabaseHandler
import discord
from discord.ext import commands
from cogs.constants import EXTENTIONS

class VeloxBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=os.getenv("APPLICATION_ID"))
        self.db = DatabaseHandler()
        self.db.createDatabase()

    async def setup_hook(self):
        for extention in EXTENTIONS:
            await bot.load_extension(extention)

bot = VeloxBot()
#load_dotenv("./vars.env")   # Uncomment this line for local development
bot.run(os.getenv("TOKEN"))