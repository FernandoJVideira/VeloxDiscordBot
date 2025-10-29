import discord
from discord.ext import commands
from cogs.Events.EventUtils import EventUtils
from cogs.constants import (
    EventTypes,
)
from cogs.DatabaseHandler import DatabaseHandler

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_utils = EventUtils(bot)
        self.database = bot.db


    async def log_event(self, event_type, guild_id, *args) -> None:
        if not await self.is_logging_enabled(guild_id):
            return

        #* Gets the log channel from the database
        log_channel = await self.event_utils.get_channel("log_channel_id", "logsettings", guild_id)

        if not log_channel:
            return

        log_embed = await self.create_log_embed(event_type, guild_id, *args)
        if log_embed:
            await log_channel.send(embed=log_embed)

    async def is_logging_enabled(self, guild_id) -> bool:
        #* Checks if logging is enabled for the guild
        query = "SELECT is_enabled FROM logsettings WHERE guild_id = ?"
        result = self.database.fetch_one_from_db(query, (guild_id,))

        if not result or not self.database.extract_value(result):
            return False

        return True

    async def create_log_embed(self, event_type, guild_id, *args) -> discord.Embed:
        #* Gets the guild
        guild = self.bot.get_guild(guild_id)

        if event_type == EventTypes.MEMBER_JOIN and args:
            return discord.Embed(
                title="Member Join",
                description=f"{args[0].mention} has joined the server!",
                color=discord.Color.green()
            )
        elif event_type == EventTypes.MEMBER_LEAVE and args:
            return discord.Embed(
                title="Member Left the Server",
                description=f"{args[0].mention} has left the server!",
                color=discord.Color.red()
            )
        elif event_type == EventTypes.MEMBER_BAN and args:
            return discord.Embed(
                title="Member Banned",
                description=f"{args[0].mention} has been banned from the server!",
                color=discord.Color.red()
            )
        elif event_type == EventTypes.MEMBER_UNBAN and args:
            return discord.Embed(
                title="Member Unbanned",
                description=f"{args[0].mention} has been unbanned from the server!",
                color=discord.Color.green()
            )
        elif event_type == EventTypes.MEMBER_KICK and args:
            return discord.Embed(
                title="Member Kicked",
                description=f"{args[0].mention} has been kicked from the server!",
                color=discord.Color.red()
            )
        elif event_type == EventTypes.MEMBER_UPDATE and args:
            return discord.Embed(
                title="Member Updated",
                description=f"{args[0].mention} has updated their profile!",
                color=discord.Color.blue()
            )
        else:
            return discord.Embed(
                title="Unknown Event",
                description="An unknown event occurred.",
                color=discord.Color.gray()
            )


async def setup(bot):
    await bot.add_cog(Logger(bot))
