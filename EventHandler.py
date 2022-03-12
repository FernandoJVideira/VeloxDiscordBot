import discord
from discord.ext import commands

intents = discord.Intents().all()
bot = commands.Bot(command_prefix = '!!', intents = intents)


class eventHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()   
    async def on_ready(self):
        print("Ready!")

    @commands.Cog.listener() 
    async def on_raw_reaction_add(self, payload : discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        emoji = payload.emoji.name
        message_id = payload.message_id
        
        if emoji == "✅" and message_id == 540663897317965834:
            role = discord.utils.get(guild.roles, name = "👻Souls👻")
            await payload.member.add_roles(role)

    @commands.Cog.listener() 
    async def on_raw_reaction_remove(self, payload : discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        emoji = payload.emoji.name
        message_id = payload.message_id
        member = await guild.fetch_member(payload.user_id)

        if emoji == "✅" and message_id == 540663897317965834:
            role = discord.utils.get(guild.roles, name = "👻Souls👻")
            await member.remove_roles(role)

def setup(bot):
    bot.add_cog(eventHandler(bot))