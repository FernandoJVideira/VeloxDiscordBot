import os
#from dotenv import load_dotenv   # Uncomment this line for local development
import sqlite3
import discord
from discord.ext import commands

EXTENTIONS = ["cogs.Sync", "cogs.MusicBot", "cogs.EventHandler", "cogs.CommandHandler"]
DATABASE_FILE = "botDB.sql"
DATABASE = "bot.db"
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=os.getenv("APPLICATION_ID"))
        self.createDatabase()

    async def setup_hook(self):
        for extention in EXTENTIONS:
            await bot.load_extension(extention)

    def createDatabase(self):
        with open(DATABASE_FILE, 'r') as sql_file:
            sql_script = sql_file.read()
            db = sqlite3.connect(DATABASE)
            cursor = db.cursor()
            cursor.executescript(sql_script)
            db.commit()
            db.close()

bot = MyBot()
#load_dotenv("./vars.env")   # Uncomment this line for local development
bot.run(os.getenv("TOKEN"))