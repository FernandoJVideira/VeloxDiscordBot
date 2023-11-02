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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guildchannel = discord.utils.get(guild.channels, name="welcome")
        dmchannel = await member.create_dm()
        await dmchannel.send(f"Welcome to **{guild.name}**! Have fun!")

        if guildchannel is not None:
            # Welcome Embed
            MyEmbed = discord.Embed(
                title="👋 Welcomeee!", description=f"{member.mention}! Welcome to the shitshowww!", color=discord.Colour.orange())
            MyEmbed.set_author(
                name=f"{member.name} #{member.discriminator}", icon_url=member.display_avatar.url)
            MyEmbed.set_thumbnail(url=member.display_avatar.url)
            MyEmbed.set_image(
                url="https://media.giphy.com/media/61XS37iBats8J3QLwF/giphy.gif")
            MyEmbed.set_footer(text=f"ID: {member.id}")

            await guildchannel.send(member.mention, embed=MyEmbed)


async def setup(bot):
    await bot.add_cog(eventHandler(bot), guilds=[1169255234598600804])
