import discord
from discord import app_commands
import random
from datetime import datetime
from discord.ext import commands

class CommandHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #Fun Commands
    @app_commands.command(name="ping", description="Pings the bot")
    async def ping(self, ctx : discord.Interaction):
        await ctx.response.send_message(f"Pong! 🏓  {self.bot.latency * 1000:.0f}ms")

    @app_commands.command(name="coinflip", description="Flips a coin")
    async def coinflip(self,ctx : discord.Interaction):
        num = random.randint(1, 2)
        if num == 1:
            await ctx.response.send_message("Heads!")
        if num == 2:
            await ctx.response.send_message("Tails!")

    @app_commands.command(name = "dice", description="Rolls a dice in NdN format. Example: 1d6")
    @app_commands.describe(dice = "The dice to roll in NdN format. Example: 1d6")
    async def dice(self, ctx : discord.Interaction, dice: str):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.response.send_message('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.response.send_message(result)

    @app_commands.command(name="rps", description="Plays Rock Paper Scissors with you")
    @app_commands.describe(hand = "Choose between ✌️, ✋ or 🤜")
    async def rps(self,ctx : discord.Interaction, hand : str):

        hands = ["✌️","✋","🤜"]
        handExist = hand in hands
        bothand = random.choice(hands)

        if handExist:
            await ctx.response.send_message(bothand)
            if hand == bothand:    
                await ctx.response.send_message("It's a Draw!")

            elif hand == "✌️":
                if bothand == "🤜":
                    await ctx.response.send_message("I won!")
                if bothand == "✋":
                    await ctx.response.send_message("You won!")

            elif hand == "✋":
                if bothand == "✌️":
                    await ctx.response.send_message("I won!")
                if bothand == "🤜":
                     await ctx.response.send_message("You won!")        

            elif hand == "🤜":
                if bothand == "✋":
                    await ctx.response.send_message("I won!")
                if bothand == "✌️":
                    await ctx.response.send_message("You won!") 

        else: 
            await ctx.response.send_message("Please insert a valid play!")

    @app_commands.command(name="help", description="Shows the bot's commands")
    async def help(self,ctx : discord.Interaction):
        #Fun Commands Embed
        MyEmbed = discord.Embed(title = "Fun Commands", description = "These are the bot's Fun commands", color = discord.Colour.orange())
        MyEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        #MyEmbed.add_field(name = "Bot Prefix", value = "The bot's Prefix is .ds", inline = False)
        MyEmbed.add_field(name = "Fun Commands", value = "Some Fun Bot Commands", inline = False)
        MyEmbed.add_field(name = "/ping", value = "The bot replies with Pong!", inline = False)
        MyEmbed.add_field(name = "/coinflip", value = "This command lets you flip a coin", inline = False)
        MyEmbed.add_field(name = "/rps ✌️/🤜/✋", value = "This comand allows to play a game of rock paper scissors with the bot", inline = False)
        
        #Music Commands Embed
        MusicEmbed = discord.Embed(title = "Music Commands", description = "These are the Bot's Music Commands", color = discord.Colour.orange())
        MusicEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        #MusicEmbed.add_field(name = ".ds join", value = "This comand makes the bot join the voice channel you're in! ", inline = False)
        MusicEmbed.add_field(name = "/play", value = "This comand makes the bot Play a song when in a voice channel! ", inline = False)
        #MusicEmbed.add_field(name = ".ds skip", value = "This comand skips to the queue's next song!", inline = False)
        MusicEmbed.add_field(name = "/pause", value = "This comand pauses the song playing!", inline = False)
        MusicEmbed.add_field(name = "/resume", value = "This comand resumes the paused song!", inline = False)
        MusicEmbed.add_field(name = "/stop", value = "This comand stops the current song!", inline = False)
        MusicEmbed.add_field(name = "/queue", value = "This comand allows the user to view what songs are in queue!", inline = False)
        
        #Admin/Mod Commands
        ModEmbed = discord.Embed(title = "Moderation/Admin Commands", description = "These are the Bot's Moderation Commands", color = discord.Colour.orange())
        ModEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        ModEmbed.add_field(name = "/editserver servername", value = "Edits the server name!", inline = False)
        ModEmbed.add_field(name = "/editserver region", value = "Edits the server Region!", inline = False)
        ModEmbed.add_field(name = "/editserver createrole", value = "Creates a Role in the Server!", inline = False)
        ModEmbed.add_field(name = "/editserver createtextchannel and /editserver createvoicechannel", value = "Creates a Text/Voice Channel in the Server", inline = False)
        ModEmbed.add_field(name = "/moderation ban @user", value = "Bans a user from the server!", inline = False)
        ModEmbed.add_field(name = "/moderation kick @user", value = "Kicks a user from the server!", inline = False)
        ModEmbed.add_field(name = "/moderation mute @user", value = "Mutes a user!", inline = False)
        ModEmbed.add_field(name = "/moderation deafen @user", value = "Deafens a user in a Voice Channel!", inline = False)
        ModEmbed.add_field(name = "/moderation purge amount", value = "Clears X amount of messages from a channel!", inline = False)
        ModEmbed.add_field(name = "/moderation unban user#XXXX", value = "Unbans a user from the server!", inline = False)
        ModEmbed.add_field(name = "/moderation unmute/undeafen @user", value = "Unmutes/Undeafens a user in a Voice Channel!", inline = False)
        ModEmbed.add_field(name = "/moderation voicekick @user", value = "Kicks a user from the Voice Channel!", inline = False)
        
        #DM Creation
        await ctx.response.send_message("Check your DMs!")
        await ctx.user.create_dm()
        await ctx.user.dm_channel.send(embed = MyEmbed)
        await ctx.user.dm_channel.send(embed = MusicEmbed) 
        await ctx.user.dm_channel.send(embed = ModEmbed)   

    #Group Command EditSever

    serverGroup = app_commands.Group(name = "editserver", description="Edit Server Settings")

    @serverGroup.command(name="servername", description="Edits the Server Name")
    @app_commands.describe(input = "The new Server Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def servername(self,ctx : discord.Interaction,*,input : str):
        await ctx.guild.edit(name = input)
        await ctx.response.send_message(f"Server Name Changed to {input}")

    @serverGroup.command(name="region", description="Edits the Server Region")
    @app_commands.describe(input = "The new Server Region")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def region(self,ctx : discord.Interaction,*,input : str):
        await ctx.guild.edit(region = input)
        await ctx.response.send_message(f"Server Region Changed to {input}")

    @serverGroup.command(name="createtextchannel", description="Creates a Text Channel")
    @app_commands.describe(input = "The new Text Channel Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createtextchannel(self,ctx : discord.Interaction,*,input : str):
        await ctx.guild.create_text_channel(name = input)
        await ctx.response.send_message(f"Text Channel Created with the name {input}")

    @serverGroup.command(name="createvoicechannel", description="Creates a Voice Channel")
    @app_commands.describe(input = "The new Voice Channel Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createvoicechannel(self,ctx : discord.Interaction,*,input : str):
        await ctx.guild.create_voice_channel(name = input)
        await ctx.response.send_message(f"Voice Channel Created with the name {input}")

    @serverGroup.command(name="createrole", description="Creates a Role")
    @app_commands.describe(input = "The new Role Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createrole(self,ctx : discord.Interaction,*,input : str):
        await ctx.guild.create_role(name = input)
        await ctx.response.send_message(f"Role Created with the name {input}")

    #----------------------------------------------//----------------------------------------------#
    #Moderation Commands  
    moderationGroup = app_commands.Group(name= "moderation", description="Moderation Commands")

    @moderationGroup.command(name="kick", description="Kicks a user")
    @app_commands.describe(member = "The user to kick")
    @app_commands.checks.has_permissions(kick_members = True)
    async def kick(self,ctx : discord.Interaction, member : discord.Member, *, reason : str):
        await ctx.guild.kick(member, reason = reason)
        await ctx.response.send_message(f"Kicked {member}")

    @moderationGroup.command(name="ban", description="Bans a user")
    @app_commands.describe(member = "The user to ban", reason = "The reason for the ban")
    @app_commands.checks.has_permissions(ban_members = True)
    async def ban(self,ctx : discord.Interaction, member : discord.Member, *, reason : str):
        await ctx.guild.ban(member, reason = reason)
        await ctx.response.send_message(f"Banned {member}")

    @moderationGroup.command(name="unban", description="Unbans a user")
    @app_commands.describe(input = "User#XXXX")
    @app_commands.checks.has_permissions(ban_members = True)
    async def unban(self,ctx : discord.Interaction, *,input : str):
        name, discriminator = input.split("#")
        banned_members = await ctx.guild.bans()
        for bannedmember in banned_members:
            username = bannedmember.user.name
            disc = bannedmember.user.discriminator
            if name == username and discriminator == disc:
                await ctx.guild.unban(bannedmember.user)
                await ctx.response.send_message(f"Unbanned {username}#{disc}")
                
    @moderationGroup.command(name="purge", description="Clears X amount of messages from a channel")
    @app_commands.describe(amount = "The amount of messages to delete", day = "The day to delete from", month = "The month to delete from", year = "The year to delete from")
    @app_commands.checks.has_permissions(manage_messages = True)
    async def purge(self,ctx : discord.Interaction, amount : int, day : int = None , month : int = None, year : int = datetime.now().year):
        if amount == "/":
            if day == None or month == None:
                return
            else:
                await ctx.channel.purge(after = datetime(year, month, day))
                await ctx.response.send_message(f"Deleted all messages after {day}/{month}/{year}")
        else:
            await ctx.channel.purge(limit = int(amount) + 1)
            await ctx.response.send_message(f"Deleted {amount} messages")

    @moderationGroup.command(name="mute", description="Mutes a user")
    @app_commands.describe(user = "The user to mute")
    @app_commands.checks.has_permissions(mute_members = True)
    async def mute(self, ctx : discord.Interaction, user : discord.Member):
        await user.edit(mute = True)
        await ctx.response.send_message(f"Muted {user}")

    @moderationGroup.command(name="unmute", description="Unmutes a user")
    @app_commands.describe(user = "The user to unmute")
    @app_commands.checks.has_permissions(mute_members = True)
    async def unmute(self,ctx : discord.Interaction, user : discord.Member ):
        await user.edit(mute = False)
        await ctx.response.send_message(f"Unmuted {user}")

    @moderationGroup.command(name="deafen", description="Deafens a user")
    @app_commands.describe(user = "The user to deafen")
    @app_commands.checks.has_permissions(deafen_members = True)
    async def deafen(self,ctx : discord.Interaction, user : discord.Member):
        await user.edit(deafen = True)
        await ctx.response.send_message(f"Deafened {user}")

    @moderationGroup.command(name="undeafen", description="Undeafens a user")
    @app_commands.describe(user = "The user to undeafen")
    @app_commands.checks.has_permissions(deafen_members = True)
    async def undeafen(self,ctx : discord.Interaction, user : discord.Member):
        await user.edit(deafen = False)
        await ctx.response.send_message(f"Undeafened {user}")

    @moderationGroup.command(name="voicekick", description="Kicks a user from a Voice Channel")
    @app_commands.describe(user = "The user to kick from the Voice Channel")
    @app_commands.checks.has_permissions(kick_members = True)
    async def voicekick(self,ctx : discord.Interaction, user : discord.Member):
        await user.edit(voice_channel = None)
        await ctx.response.send_message(f"Kicked {user} from Voice Channel")

    #----------------------------------------------//----------------------------------------------#
    #Error Handlers

    #Fun Commands ErrorHandlers
    @rps.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("Please Insert ✌️/🤜/✋")

    #Moderation Commands ErrorHandlers
    @servername.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("Server Name cant be empty!")

    @region.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("Please choose a valid region!")
        if isinstance(error, app_commands.errors.CommandInvokeError):
            await ctx.response.send_message("Please choose a valid region!")

    @createtextchannel.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("Please enter a channel name!")

    @createvoicechannel.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("Please enter a channel name!")

    @kick.error
    async def errorhandler(self,ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MemberNotFound):
            await ctx.response.send_message("Please mention a valid user!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("You need to mention a user in order to use this command!")

    @ban.error
    async def errorhandler(self,ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MemberNotFound):
            await ctx.response.send_message("Please mention a valid user!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("You need to mention a user in order to use this command!")

    @purge.error
    async def errorhandler(self,ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("You have to specify either a date or an amout.")
        if isinstance(error, app_commands.errors.CommandInvokeError):
            await ctx.response.send_message("You can only have a / or a number as the 1st input.")

    @deafen.error
    async def errorhandler(self,ctx : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @undeafen.error
    async def errorhandler(self,ctx : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @mute.error
    async def errorhandler(self,ctx : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @unmute.error
    async def errorhandler(self,ctx : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @voicekick.error
    async def errorhandler(self,ctx : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
    
    @unban.error
    async def errorhandler(self,ctx : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.MemberNotFound):
            await ctx.response.send_message("Please mention a valid user!")
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await ctx.response.send_message("You need to mention a user in order to use this command!")
        
async def setup(bot) -> None:
    await bot.add_cog(CommandHandler(bot), guilds=[discord.Object(id=1169255234598600804)])
