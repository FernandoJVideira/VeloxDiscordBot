import discord
import random
from datetime import datetime
from discord.ext import commands

bot = commands.Bot(command_prefix = ".ds ", help_command = None)


class CommandHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #Fun Commands
    @commands.command()
    async def ping(self,ctx):
        await ctx.send("Pong!")

    @commands.command()
    async def coinflip(self,ctx):
        num = random.randint(1, 2)
        if num == 1:
            await ctx.send("Heads!")
        if num == 2:
            await ctx.send("Tails!")

    @commands.command()
    async def rps(self,ctx, hand):

        hands = ["✌️","✋","🤜"]
        handExist = hand in hands
        bothand = random.choice(hands)

        if handExist:
            await ctx.send(bothand)
            if hand == bothand:    
                await ctx.send("It's a Draw!")

            elif hand == "✌️":
                if bothand == "🤜":
                    await ctx.send("I won!")
                if bothand == "✋":
                    await ctx.send("You won!")

            elif hand == "✋":
                if bothand == "✌️":
                    await ctx.send("I won!")
                if bothand == "🤜":
                     await ctx.send("You won!")        

            elif hand == "🤜":
                if bothand == "✋":
                    await ctx.send("I won!")
                if bothand == "✌️":
                    await ctx.send("You won!") 

        else: 
            await ctx.send("Please insert a valid play!")

    @commands.command(aliases=["about"])
    async def help(self,ctx):
        #Fun Commands Embed
        MyEmbed = discord.Embed(title = "Fun Commands", description = "These are the bot's Fun commands", color = discord.Colour.orange())
        MyEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        MyEmbed.add_field(name = "Bot Prefix", value = "The bot's Prefix is .ds", inline = False)
        MyEmbed.add_field(name = "Fun Commands", value = "Some Fun Bot Commands", inline = False)
        MyEmbed.add_field(name = ".ds ping", value = "The bot replies with Pong!", inline = False)
        MyEmbed.add_field(name = ".ds coinflip", value = "This command lets you flip a coin", inline = False)
        MyEmbed.add_field(name = ".ds rps ✌️/🤜/✋", value = "This comand allows to play a game of rock paper scissors with the bot", inline = False)
        
        #Music Commands Embed
        MusicEmbed = discord.Embed(title = "Music Commands", description = "These are the Bot's Music Commands", color = discord.Colour.orange())
        MusicEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        MusicEmbed.add_field(name = ".ds join", value = "This comand makes the bot join the voice channel you're in! ", inline = False)
        MusicEmbed.add_field(name = ".ds play", value = "This comand makes the bot Play a song when in a voice channel! ", inline = False)
        MusicEmbed.add_field(name = ".ds skip", value = "This comand skips to the queue's next song!", inline = False)
        MusicEmbed.add_field(name = ".ds pause", value = "This comand pauses the song playing!", inline = False)
        MusicEmbed.add_field(name = ".ds resume", value = "This comand resumes the paused song!", inline = False)
        MusicEmbed.add_field(name = ".ds viewqueue", value = "This comand allows the user to view what songs are in queue!", inline = False)
        
        #Admin/Mod Commands
        ModEmbed = discord.Embed(title = "Moderation/Admin Commands", description = "These are the Bot's Moderation Commands", color = discord.Colour.orange())
        ModEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        ModEmbed.add_field(name = ".ds edit servername", value = "Edits the server name!", inline = False)
        ModEmbed.add_field(name = ".ds edit region", value = "Edit's the server Region!", inline = False)
        ModEmbed.add_field(name = ".ds edit createrole", value = "Creates a Role in the Server!", inline = False)
        ModEmbed.add_field(name = ".ds edit createtextchannel/createvoicechannel", value = "Creates a Text/Voice Channel in the Server", inline = False)
        ModEmbed.add_field(name = ".ds ban @user", value = "Bans a user from the server!", inline = False)
        ModEmbed.add_field(name = ".ds kick @user", value = "Kicks a user from the server!", inline = False)
        ModEmbed.add_field(name = ".ds mute @user", value = "Mutes a user!", inline = False)
        ModEmbed.add_field(name = ".ds deafen @user", value = "Deafens a user in a Voice Channel!", inline = False)
        ModEmbed.add_field(name = ".ds purge amount", value = "Clears X amount of messages from a channel!", inline = False)
        ModEmbed.add_field(name = ".ds unban user#XXXX", value = "Unbans a user from the server!", inline = False)
        ModEmbed.add_field(name = ".ds unmute/undeafen @user", value = "Unmutes/Undeafens a user in a Voice Channel!", inline = False)
        ModEmbed.add_field(name = ".ds voicekick @user", value = "Kicks a user from the Voice Channel!", inline = False)
        
        #DM Creation
        await ctx.author.create_dm()
        await ctx.author.dm_channel.send(embed = MyEmbed)
        await ctx.author.dm_channel.send(embed = MusicEmbed) 
        await ctx.author.dm_channel.send(embed = ModEmbed)   

    #Group Command EditSever
    @bot.group()
    async def edit(self,ctx):
        pass

    @edit.command()
    @commands.has_permissions(manage_guild = True)
    async def servername(self,ctx,*,input):
        await ctx.guild.edit(name = input)

    @edit.command()
    @commands.has_permissions(manage_guild = True)
    async def region(self,ctx,*,input):
        await ctx.guild.edit(region = input)

    @edit.command()
    @commands.has_permissions(manage_channels = True)
    async def createtextchannel(self,ctx,*,input):
        await ctx.guild.create_text_channel(name = input)

    @edit.command()
    @commands.has_permissions(manage_channels = True)
    async def createvoicechannel(self,ctx,*,input):
        await ctx.guild.create_voice_channel(name = input)

    @edit.command()
    @commands.has_permissions(manage_roles = True)
    async def createrole(self,ctx,*,input):
        await ctx.guild.create_role(name = input)

    #----------------------------------------------//----------------------------------------------#
    #Moderation Commands  

    @commands.command()
    @commands.has_permissions(kick_members = True)
    async def kick(self,ctx, member : discord.Member, *, reason = None):
        await ctx.guild.kick(member, reason = reason)

    @commands.command()
    @commands.has_permissions(ban_members = True)
    async def ban(self,ctx, member : discord.Member, *, reason = None):
        await ctx.guild.ban(member, reason = reason)
        await ctx.send(f"Banned {member}")

    @commands.command()
    @commands.has_permissions(ban_members = True)
    async def unban(self,ctx, *,input):
        name, discriminator = input.split("#")
        banned_members = await ctx.guild.bans()
        for bannedmember in banned_members:
            username = bannedmember.user.name
            disc = bannedmember.user.discriminator
            if name == username and discriminator == disc:
                await ctx.guild.unban(bannedmember.user)
                await ctx.send(f"Unbanned {username} {disc}")
                
    @commands.command()
    @commands.has_permissions(manage_messages = True)
    async def purge(self,ctx, amount, day : int = None, month : int = None, year : int = datetime.now().year):
        if amount == "/":
            if day == None or month == None:
                return
            else:
                await ctx.channel.purge(after = datetime(year, month, day))
        else:
            await ctx.channel.purge(limit = int(amount) + 1)

    @commands.command()
    @commands.has_permissions(mute_members = True)
    async def mute(ctx, user : discord.Member):
        await user.edit(mute = True)

    @commands.command()
    @commands.has_permissions(mute_members = True)
    async def unmute(self,ctx, user : discord.Member):
        await user.edit(mute = False)

    @commands.command()
    @commands.has_permissions(deafen_members = True)
    async def deafenself(self,ctx, user : discord.Member):
        await user.edit(deafen = True)

    @commands.command()
    @commands.has_permissions(deafen_members = True)
    async def undeafen(self,ctx, user : discord.Member):
        await user.edit(deafen = False)

    @commands.command()
    @commands.has_permissions(kick_members = True)
    async def voicekick(self,ctx, user : discord.Member):
        await user.edit(voice_channel = None)

    #----------------------------------------------//----------------------------------------------#
    #Error Handlers

    #Fun Commands ErrorHandlers
    @rps.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please Insert ✌️/🤜/✋")

    #Moderation Commands ErrorHandlers
    @servername.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Server Name cant be empty!")

    @region.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please choose a valid region!")
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please choose a valid region!")

    @createtextchannel.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a channel name!")

    @createvoicechannel.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a channel name!")

    @kick.error
    async def errorhandler(self,ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Please mention a valid user!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to mention a user in order to use this command!")

    @ban.error
    async def errorhandler(self,ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Please mention a valid user!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to mention a user in order to use this command!")

    @purge.error
    async def errorhandler(self,ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You have to specify either a date or an amout.")
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("You can only have a / or a number as the 1st input.")
            
        
def setup(bot):
    bot.add_cog(CommandHandler(bot))