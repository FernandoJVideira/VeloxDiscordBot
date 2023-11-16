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
        for extention in ["cogs.EventHandler", "cogs.CommandHandler"]:
            await bot.load_extension(extention)
        await self.tree.sync()

    def createDatabase(self):
        database = sqlite3.connect("bot.db")
        cursor = database.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS levels (level INT, xp INT, user INT, guild INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS twitch (twitch_user TEXT, status TEXT , guild_id INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS levelsettings (levelsys BOOL, role INT, levelreq INT, message TEXT ,guild_id INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS welcome (guild_id INT, welcome_channel_id INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS levelup (guild_id INT, levelup_channel_id INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS twitch_config (guild_id INT, twitch_channel_id INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS rps (guild_id INT, user_id INT, score INT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS defaultrole (guild_id INT, role_id INT)")
        database.commit()

bot = MyBot()
load_dotenv("./vars.env")
bot.run(os.getenv("TOKEN"))