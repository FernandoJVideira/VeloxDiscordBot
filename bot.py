import nextcord
from nextcord import Interaction


intents = nextcord.Intents().all()
from nextcord.ext import commands, application_checks

bot = commands.Bot(command_prefix = ".ds ", help_command = None, intents = intents)

bot.load_extension("MusicBot")
bot.load_extension("EventHandler")
bot.load_extension("CommandHandler")
#bot.load_extension("MusicCommands")

def is_me(ctx : Interaction):
    return ctx.message.author.id == 249679918047166464

@bot.event
async def on_member_join(member):
    guild = member.guild
    guildchannel = nextcord.utils.get(guild.channels, name = "・🎉┊boas-vindas")
    dmchannel = await member.create_dm()
    await dmchannel.send(f"Welcome to **{guild.name}**! Have fun!")

    if guildchannel is not None:
        #Welcome Embed
        MyEmbed = nextcord.Embed(title = "👋 Bem Vindo(a)!", description = f"Olá {member.mention}, espero que te divirtas no server {guild.name}", color = nextcord.Colour.orange())
        MyEmbed.set_author(name = f"{member.name} #{member.discriminator}", icon_url = member.display_avatar.url)
        MyEmbed.set_thumbnail(url = member.display_avatar.url)
        MyEmbed.set_image(url = "https://media.giphy.com/media/61XS37iBats8J3QLwF/giphy.gif")
        MyEmbed.set_footer(text = f"ID: {member.id}")
        
        await guildchannel.send(member.mention, embed = MyEmbed)

@bot.slash_command(name="reloadevents", description="Reloads the EventHandler")
@application_checks.check(is_me)
async def reloadevents(ctx : Interaction):
    await ctx.send("Reloading EventHandler")
    bot.reload_extension("EventHandler")
    
@bot.slash_command(name="reloadcommands", description="Reloads the CommandHandler")
@application_checks.check(is_me)
async def reloadcommands(ctx : Interaction):
    await ctx.send("Reloading CommandHandler")
    bot.reload_extension("CommandHandler")
    
@bot.slash_command(name="reloadmusic", description="Reloads the MusicHandler")
@application_checks.check(is_me)
async def reloadmusic(ctx : Interaction):
    await ctx.send("Reloading MusicHandler")
    bot.reload_extension("MusicBot")


bot.run('NDQ3NDI0MTgxMTM1NjA1ODAw.G4vZBN.sM34slbM8L3CwrP4Wkf2KgoieyaknDSyA67ZQQ')
#bot.run("MTA0MTcxMDY5NTY4ODk4MjU0MA.GJ_7v_.Ys39LTmoGPMdxV29n1-uetcCXCKh8DsBr86X_Q")