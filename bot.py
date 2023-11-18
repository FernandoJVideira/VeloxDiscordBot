import os
from dotenv import load_dotenv
import sqlite3
import discord
from discord.ext import commands
class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=".",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=os.getenv("APPLICATION_ID"))
        self.createDatabase()

    async def setup_hook(self):
        for extention in ["cogs.MusicBot","cogs.EventHandler", "cogs.CommandHandler"]:
            await bot.load_extension(extention)
        await self.tree.sync()

    def createDatabase(self):
        with open('botDB.sql', 'r') as sql_file:
            sql_script = sql_file.read()
            db = sqlite3.connect('bot.db')
            cursor = db.cursor()
            cursor.executescript(sql_script)
            db.commit()
            db.close()

bot = MyBot()
load_dotenv("./vars.env")
bot.run(os.getenv("TOKEN"))