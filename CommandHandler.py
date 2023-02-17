import nextcord
from nextcord import Interaction, SlashOption
import random
from datetime import datetime
from nextcord.ext import commands, application_checks

intents = nextcord.Intents().all()

bot = commands.Bot(command_prefix = ".ds ", help_command = None, intents = intents)

class CommandHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #Fun Commands
    @bot.slash_command(name= "ping", description="Pings the bot")
    async def ping(self, ctx : Interaction):
        await ctx.send(f"Pong! 🏓  {self.bot.latency * 1000:.0f}ms")

    @bot.slash_command(description="Flips a coin")
    async def coinflip(self,ctx : Interaction):
        num = random.randint(1, 2)
        if num == 1:
            await ctx.send("Heads!")
        if num == 2:
            await ctx.send("Tails!")

    @bot.slash_command(name = "dice", description="Rolls a dice in NdN format. Example: 1d6")
    async def dice(self, ctx : Interaction, dice: str = SlashOption(description="The dice you want to roll. Example: 1d6")):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.send('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(result)

    @bot.slash_command(name = "rps", description="Plays Rock Paper Scissors with you")
    async def rps(self,ctx : Interaction, hand : str = SlashOption(description="Choose between ✌️, ✋ or 🤜")):

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

    @bot.slash_command(name ="help", description="Shows the bot's commands")
    async def help(self,ctx : Interaction):
        #Fun Commands Embed
        MyEmbed = nextcord.Embed(title = "Fun Commands", description = "These are the bot's Fun commands", color = nextcord.Colour.orange())
        MyEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        #MyEmbed.add_field(name = "Bot Prefix", value = "The bot's Prefix is .ds", inline = False)
        MyEmbed.add_field(name = "Fun Commands", value = "Some Fun Bot Commands", inline = False)
        MyEmbed.add_field(name = "/ping", value = "The bot replies with Pong!", inline = False)
        MyEmbed.add_field(name = "/coinflip", value = "This command lets you flip a coin", inline = False)
        MyEmbed.add_field(name = "/rps ✌️/🤜/✋", value = "This comand allows to play a game of rock paper scissors with the bot", inline = False)
        
        #Music Commands Embed
        MusicEmbed = nextcord.Embed(title = "Music Commands", description = "These are the Bot's Music Commands", color = nextcord.Colour.orange())
        MusicEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        #MusicEmbed.add_field(name = ".ds join", value = "This comand makes the bot join the voice channel you're in! ", inline = False)
        MusicEmbed.add_field(name = "/play", value = "This comand makes the bot Play a song when in a voice channel! ", inline = False)
        #MusicEmbed.add_field(name = ".ds skip", value = "This comand skips to the queue's next song!", inline = False)
        MusicEmbed.add_field(name = "/pause", value = "This comand pauses the song playing!", inline = False)
        MusicEmbed.add_field(name = "/resume", value = "This comand resumes the paused song!", inline = False)
        MusicEmbed.add_field(name = "/stop", value = "This comand stops the current song!", inline = False)
        MusicEmbed.add_field(name = "/queue", value = "This comand allows the user to view what songs are in queue!", inline = False)
        
        #Admin/Mod Commands
        ModEmbed = nextcord.Embed(title = "Moderation/Admin Commands", description = "These are the Bot's Moderation Commands", color = nextcord.Colour.orange())
        ModEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        ModEmbed.add_field(name = "/servername", value = "Edits the server name!", inline = False)
        ModEmbed.add_field(name = "/region", value = "Edits the server Region!", inline = False)
        ModEmbed.add_field(name = "/createrole", value = "Creates a Role in the Server!", inline = False)
        ModEmbed.add_field(name = "/createtextchannel and /createvoicechannel", value = "Creates a Text/Voice Channel in the Server", inline = False)
        ModEmbed.add_field(name = "/ban @user", value = "Bans a user from the server!", inline = False)
        ModEmbed.add_field(name = "/kick @user", value = "Kicks a user from the server!", inline = False)
        ModEmbed.add_field(name = "/mute @user", value = "Mutes a user!", inline = False)
        ModEmbed.add_field(name = "/deafen @user", value = "Deafens a user in a Voice Channel!", inline = False)
        ModEmbed.add_field(name = "/purge amount", value = "Clears X amount of messages from a channel!", inline = False)
        ModEmbed.add_field(name = "/unban user#XXXX", value = "Unbans a user from the server!", inline = False)
        ModEmbed.add_field(name = "/unmute/undeafen @user", value = "Unmutes/Undeafens a user in a Voice Channel!", inline = False)
        ModEmbed.add_field(name = "/voicekick @user", value = "Kicks a user from the Voice Channel!", inline = False)
        
        #DM Creation
        await ctx.user.create_dm()
        await ctx.user.dm_channel.send(embed = MyEmbed)
        await ctx.user.dm_channel.send(embed = MusicEmbed) 
        await ctx.user.dm_channel.send(embed = ModEmbed)   

    #Group Command EditSever

    @bot.slash_command(name="servername", description="Edits the Server Name")
    @application_checks.has_permissions(manage_guild = True)
    async def servername(self,ctx : Interaction,*,input : str = SlashOption(description="Server Name")):
        await ctx.guild.edit(name = input)
        await ctx.send(f"Server Name Changed to {input}")

    @bot.slash_command(name="region", description="Edits the Server Region")
    @application_checks.has_permissions(manage_guild = True)
    async def region(self,ctx : Interaction,*,input : str = SlashOption(description="Region Name")):
        await ctx.guild.edit(region = input)
        await ctx.send(f"Server Region Changed to {input}")

    @bot.slash_command(name="createtextchannel", description="Creates a Text Channel")
    @application_checks.has_permissions(manage_guild = True)
    async def createtextchannel(self,ctx : Interaction,*,input : str = SlashOption(description="Channel Name")):
        await ctx.guild.create_text_channel(name = input)
        await ctx.send(f"Text Channel Created with the name {input}")

    @bot.slash_command(name="createvoicechannel", description="Creates a Voice Channel")
    @application_checks.has_permissions(manage_guild = True)
    async def createvoicechannel(self,ctx : Interaction,*,input : str = SlashOption(description="Channel Name")):
        await ctx.guild.create_voice_channel(name = input)
        await ctx.send(f"Voice Channel Created with the name {input}")

    @bot.slash_command(name="createrole", description="Creates a Role")
    @application_checks.has_permissions(manage_guild = True)
    async def createrole(self,ctx : Interaction,*,input : str = SlashOption(description="Role Name")):
        await ctx.guild.create_role(name = input)
        await ctx.send(f"Role Created with the name {input}")

    #----------------------------------------------//----------------------------------------------#
    #Moderation Commands  

    @bot.slash_command(name="kick", description="Kicks a user")
    @application_checks.has_permissions(kick_members = True)
    async def kick(self,ctx : Interaction, member : nextcord.Member, *, reason = SlashOption(description="Reason to kick")):
        await ctx.guild.kick(member, reason = reason)
        await ctx.send(f"Kicked {member}")

    @bot.slash_command(name="ban", description="Bans a user")
    @application_checks.has_permissions(ban_members = True)
    async def ban(self,ctx : Interaction, member : nextcord.Member, *, reason = SlashOption(description="Reason for ban")):
        await ctx.guild.ban(member, reason = reason)
        await ctx.send(f"Banned {member}")

    @bot.slash_command(name="unban", description="Unbans a user")
    @application_checks.has_permissions(ban_members = True)
    async def unban(self,ctx : Interaction, *,input : str = SlashOption(description="User#XXXX")):
        name, discriminator = input.split("#")
        banned_members = await ctx.guild.bans()
        for bannedmember in banned_members:
            username = bannedmember.user.name
            disc = bannedmember.user.discriminator
            if name == username and discriminator == disc:
                await ctx.guild.unban(bannedmember.user)
                await ctx.send(f"Unbanned {username}#{disc}")
                
    @bot.slash_command(name="purge", description="Purges messages from a channel")
    @application_checks.has_permissions(manage_messages = True)
    async def purge(self,ctx : Interaction, amount = SlashOption(description="Amount of messages to purge"), day : int = None , month : int = None, year : int = datetime.now().year):
        if amount == "/":
            if day == None or month == None:
                return
            else:
                await ctx.channel.purge(after = datetime(year, month, day))
                await ctx.send(f"Deleted all messages after {day}/{month}/{year}")
        else:
            await ctx.channel.purge(limit = int(amount) + 1)
            await ctx.send(f"Deleted {amount} messages")

    @bot.slash_command(name="mute", description="Mutes a user")
    @application_checks.has_permissions(mute_members = True)
    async def mute(self, ctx : Interaction, user : nextcord.Member = SlashOption(description="User to mute")):
        await user.edit(mute = True)
        await ctx.send(f"Muted {user}")

    @bot.slash_command(name="unmute", description="Unmutes a user")
    @application_checks.has_permissions(mute_members = True)
    async def unmute(self,ctx : Interaction, user : nextcord.Member = SlashOption(description="User to unmute")):
        await user.edit(mute = False)
        await ctx.send(f"Unmuted {user}")

    @bot.slash_command(name="deafenself", description="Deafens a user")
    @application_checks.has_permissions(deafen_members = True)
    async def deafenself(self,ctx : Interaction, user : nextcord.Member = SlashOption(description="User to deafen")):
        await user.edit(deafen = True)
        await ctx.send(f"Deafened {user}")

    @bot.slash_command(name="undeafen", description="Undeafens a user")
    @application_checks.has_permissions(deafen_members = True)
    async def undeafen(self,ctx : Interaction, user : nextcord.Member = SlashOption(description="User to undeafen")):
        await user.edit(deafen = False)
        await ctx.send(f"Undeafened {user}")

    @bot.slash_command(name="voicekick", description="Kicks a user from the Voice Channel")
    @application_checks.has_permissions(kick_members = True)
    async def voicekick(self,ctx : Interaction, user : nextcord.Member = SlashOption(description="User to kick from Voice Channel")):
        await user.edit(voice_channel = None)
        await ctx.send(f"Kicked {user} from Voice Channel")

    #----------------------------------------------//----------------------------------------------#
    #Error Handlers

    #Fun Commands ErrorHandlers
    @rps.error
    async def errorhandler(self, ctx : Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please Insert ✌️/🤜/✋")

    #Moderation Commands ErrorHandlers
    @servername.error
    async def errorhandler(self, ctx : Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Server Name cant be empty!")

    @region.error
    async def errorhandler(self, ctx : Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please choose a valid region!")
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Please choose a valid region!")

    @createtextchannel.error
    async def errorhandler(self, ctx : Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a channel name!")

    @createvoicechannel.error
    async def errorhandler(self, ctx : Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a channel name!")

    @kick.error
    async def errorhandler(self,ctx : Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Please mention a valid user!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to mention a user in order to use this command!")

    @ban.error
    async def errorhandler(self,ctx : Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!")
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Please mention a valid user!")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to mention a user in order to use this command!")

    @purge.error
    async def errorhandler(self,ctx : Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You have to specify either a date or an amout.")
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("You can only have a / or a number as the 1st input.")

        
def setup(bot):
    bot.add_cog(CommandHandler(bot))
