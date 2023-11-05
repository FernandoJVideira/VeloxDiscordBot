import os
#from dotenv import load_dotenv
import discord
from discord.ext import commands
class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=".ds ",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=os.getenv("APPLICATION_ID"))

    async def setup_hook(self):
        for extention in ["cogs.MusicBot", "cogs.EventHandler", "cogs.CommandHandler"]:
            await bot.load_extension(extention)
        await self.tree.sync()

bot = MyBot()
#load_dotenv("./vars.env")
bot.run(os.getenv("TOKEN"))