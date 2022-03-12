import discord

intents = discord.Intents().all()
from discord.ext import commands

bot = commands.Bot(command_prefix = "!!", help_command = None, intents = intents)

def is_me(ctx):
    return ctx.author.id == 249679918047166464

@bot.event
async def on_member_join(member):
    guild = member.guild
    guildname = guild.name
    dmchannel = await member.create_dm()
    await dmchannel.send(f"Welcome to {guildname}! Please read the rules carefully, respect them and have fun")

@bot.command()
@commands.check(is_me)
async def reloadevents(ctx):
    await ctx.send("Reloading EventHandler")
    bot.reload_extension("EventHandler")
    
@bot.command()
@commands.check(is_me)
async def reloadcommands(ctx):
    await ctx.send("Reloading CommandHandler")
    bot.reload_extension("CommandHandler")
    
@bot.command()
@commands.check(is_me)
async def reloadmusic(ctx):
    await ctx.send("Reloading MusicHandler")
    bot.reload_extension("MusicCommands")

bot.load_extension("CommandHandler")
bot.load_extension("EventHandler")
bot.load_extension("MusicCommands")   
bot.run("NDQ3NDI0MTgxMTM1NjA1ODAw.WwBGPQ.ScAkseYjEAKAb2BhJsjfJz7AKeQ")