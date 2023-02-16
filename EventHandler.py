import nextcord
from nextcord.ext import commands
import MusicBot

intents = nextcord.Intents().all()
bot = commands.Bot(command_prefix = '.ds ', intents = intents)


class eventHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()   
    async def on_ready(self):
        print("Ready!")

    @commands.Cog.listener() 
    async def on_raw_reaction_add(self, payload : nextcord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        emoji = payload.emoji.name
        message_id = payload.message_id
        
        #TODO : change message_id to the message id of the message you want to react to
        if emoji == "✅" and message_id == 1074787938354864311:
            role = nextcord.utils.get(guild.roles, name = "👤| Membro")
            await payload.member.add_roles(role)

    @commands.Cog.listener() 
    async def on_raw_reaction_remove(self, payload : nextcord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        emoji = payload.emoji.name
        message_id = payload.message_id
        member = await guild.fetch_member(payload.user_id)

        #TODO : change message_id to the message id of the message you want to react to
        if emoji == "✅" and message_id == 1074787938354864311:
            role = nextcord.utils.get(guild.roles, name = "👤| Membro")
            await member.remove_roles(role)

def setup(bot):
    bot.add_cog(eventHandler(bot))
