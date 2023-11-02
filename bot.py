import os
import discord
from discord.ext import commands


class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=".ds ",
            help_command=None,
            intents=discord.Intents.all(),
            application_id=1169299903378378772)

    async def setup_hook(self):
        for extention in ["cogs.MusicBot", "cogs.EventHandler", "cogs.CommandHandler"]:
            await bot.load_extension(extention)

        await bot.tree.sync(guild=discord.Object(id=1169255234598600804))

    async def on_ready(self):
        print("Ready for action!")

bot = MyBot()

bot.run(os.getenv("TOKEN"))
