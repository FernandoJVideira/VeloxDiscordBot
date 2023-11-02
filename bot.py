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
        print("Bot is ready")

bot = MyBot()

@bot.event
async def on_member_join(member):
    guild = member.guild
    guildchannel = discord.utils.get(guild.channels, name="welcome")
    dmchannel = await member.create_dm()
    await dmchannel.send(f"Welcome to **{guild.name}**! Have fun!")

    if guildchannel is not None:
        # Welcome Embed
        MyEmbed = discord.Embed(
            title="👋 Bem Vindo(a)!", description=f"Olá {member.mention}, espero que te divirtas no server {guild.name}", color=discord.Colour.orange())
        MyEmbed.set_author(
            name=f"{member.name} #{member.discriminator}", icon_url=member.display_avatar.url)
        MyEmbed.set_thumbnail(url=member.display_avatar.url)
        MyEmbed.set_image(
            url="https://media.giphy.com/media/61XS37iBats8J3QLwF/giphy.gif")
        MyEmbed.set_footer(text=f"ID: {member.id}")

        await guildchannel.send(member.mention, embed=MyEmbed)


bot.run(os.getenv("TOKEN"))