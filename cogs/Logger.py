import discord
from discord.ext import commands

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    