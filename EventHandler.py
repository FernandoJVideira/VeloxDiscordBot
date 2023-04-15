import nextcord
from nextcord.ext import commands

intents = nextcord.Intents().all()
bot = commands.Bot(command_prefix='.ds ', intents=intents)
ROLE_ID = 1074785999336509565  # TODO: change this to database connection


class eventHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        global ROLE_ID
        guild = after.guild

        if before.pending and not after.pending:
            role = guild.get_role(ROLE_ID)
            await after.add_roles(role)


def setup(bot):
    bot.add_cog(eventHandler(bot))
