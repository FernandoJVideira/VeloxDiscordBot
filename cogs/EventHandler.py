import discord
from discord.ext import commands

ROLE_ID = 1169285656602755092  # TODO: change this to database connection


class eventHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        global ROLE_ID
        guild = after.guild

        if before.pending and not after.pending:
            role = guild.get_role(ROLE_ID)
            await after.add_roles(role)


async def setup(bot):
    await bot.add_cog(eventHandler(bot))
