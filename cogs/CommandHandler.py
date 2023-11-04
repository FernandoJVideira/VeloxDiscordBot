import discord
from discord import app_commands
from discord.app_commands import Choice
import random
from datetime import datetime
from discord.ext import commands, tasks
import sqlite3
from easy_pil import *

database = sqlite3.connect("bot.db")
cursor = database.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS welcome (guild_id INT, welcome_channel_id INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS levelup (guild_id INT, levelup_channel_id INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS twitch_config (guild_id INT, twitch_channel_id INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS rps (guild_id INT, user_id INT, score INT)")
class CommandHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.numbers = ["1️⃣","2️⃣","3️⃣","4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣","9️⃣","🔟"]

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

    @app_commands.command(name="poll", description="Starts a Poll!")
    @app_commands.describe(title = "The question to ask, has to be in quotation marks", options = 'The options to choose from in the format "Option1 Option2 Option3"')
    @app_commands.checks.has_permissions(manage_messages = True)
    async def poll(self, ctx : discord.Interaction, minutes : int, title: str, options : str):
        options = options.split()
        await ctx.response.send_message("Starting poll...")
        if options[0] == "-":
            pollEmbed = discord.Embed(title = title, description = f"You have **{minutes}** minutes remaining!", color = discord.Colour.orange())
            msg = await ctx.channel.send(embed = pollEmbed)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
        else:
            pollEmbed = discord.Embed(title = title, description = f"You have **{minutes}** minutes remaining!", color=discord.Colour.orange())
            for number,option in enumerate(options):
                pollEmbed.add_field(name = f"{self.numbers[number]}", value = f"**{option}**", inline = False)
            msg = await ctx.channel.send(embed = pollEmbed)
            for x in range(len(pollEmbed.fields)):
                await msg.add_reaction(self.numbers[x])

        self.poll_loop.start(ctx, minutes, title, options, msg)

    @tasks.loop(minutes = 1)
    async def poll_loop(self, ctx, minutes, title, options, msg):

        count = self.poll_loop.current_loop
        remainingTime = minutes - count

        newEmbed = discord.Embed(title = title, description = f"You have **{remainingTime}** minutes remaining!", color=discord.Colour.orange())
        if options[0] == "-":
            await msg.edit(embed = newEmbed)
        else:
            for number,option in enumerate(options):
                newEmbed.add_field(name = f"{self.numbers[number]}", value = f"**{option}**", inline = False)
            await msg.edit(embed = newEmbed)

        if remainingTime == 0:
            counts = []
            msg = discord.utils.get(self.bot.cached_messages,id = msg.id)
            reactions = msg.reactions

            for reaction in reactions:
                counts.append(reaction.count)
            max_value = max(counts)
            i=0
            for count in counts:
                if count == max_value:
                    i = i + 1
            if i > 1:
                await ctx.channel.send("It's a draw!")
            else:
                max_index = counts.index(max_value)

                if options[0] == "-":
                    winnerEmoji = reactions[max_index]
                    await ctx.channel.send("Time's Up!")
                    if winnerEmoji.emoji == "👍":
                        await ctx.channel.send("Looks like people think that way!")
                    if winnerEmoji.emoji == "👎":
                        await ctx.channel.send("Looks like people don't think that way!")
                else:
                    winner = options[max_index]
                    winnerEmoji = reactions[max_index]

                    await ctx.channel.send("Time's Up!")
                    await ctx.channel.send(f"{winnerEmoji.emoji} - **{winner}** has won the Poll!")

            self.poll_loop.stop()

    @app_commands.command(name= "rank", description="Shows your level!")
    async def rank(self, ctx : discord.Interaction, member: discord.Member = None):
        if member is None:
            member = ctx.user
        xp = cursor.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (member.id, ctx.guild.id)).fetchone()
        level = cursor.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (member.id, ctx.guild.id)).fetchone()

        if not xp or not level:
            cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)", (0,0,member.id, ctx.guild.id))
            database.commit()
        try:
            xp = xp[0]
            level = level[0]
        except TypeError:
            xp = 0
            level = 0

        userData = {
            "name" : member.display_name,
            "xp" : xp,
            "level" : level,
            "nextLevelXp" : 100,
            "precentage" : xp
        }

        background = Editor(Canvas((900, 300), color="#141414"))
        profilePicture = await load_image_async(str(member.avatar.url))
        profile = Editor(profilePicture).resize((150, 150)).circle_image()

        poppins = Font.poppins(size=40)
        poppins_small = Font.poppins(size=30)

        cardRightShape = [(600, 0), (750, 300), (900, 300), (900, 0)]

        background.polygon(cardRightShape, color="#FFFFFF")
        background.paste(profile, (30,30))

        background.rectangle((30, 220), width=650, height=40, color="#FFFFFF", radius=20)
        background.bar((30, 220), max_width=650, height=40, percentage=userData["precentage"], color="#282828", radius=20)
        background.text((200, 40), userData["name"], font=poppins, color="#FFFFFF")

        background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
        background.text((200, 130), f"Level - {userData['level']} | XP - {int(userData['xp'])}%", font=poppins_small, color="#FFFFFF")

        file = discord.File(fp=background.image_bytes, filename="levelcard.png")
        await ctx.response.send_message(file=file)

    @app_commands.command(name="rps", description="Plays Rock Paper Scissors with you")
    @app_commands.describe(hand = "Choose between ✌️, ✋ or 🤜")
    @app_commands.choices(hand = [
        Choice(name = "Scissors", value = "✌️"),
        Choice(name = "Paper", value = "✋"),
        Choice(name = "Rock", value = "🤜"),
        ])
    async def rps(self,ctx : discord.Interaction, hand : str):

        hands = ["✌️","✋","🤜"]
        handExist = hand in hands
        bothand = random.choice(hands)

        if handExist:
            score = cursor.execute("SELECT score FROM rps WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.user.id)).fetchone()
            
            if score is not None:
                score = score[0]
            else:
                cursor.execute("INSERT INTO rps VALUES (?,?,?)", (ctx.guild.id, ctx.user.id, 0))
                database.commit()
                score = 0

            if hand == bothand:    
                embed = discord.Embed(title = "It's a Draw!", description = "You and I chose the same hand!", color = discord.Colour.orange())
                embed.add_field(name = "You chose:", value = hand, inline = False)
                embed.add_field(name = "I chose:", value = bothand, inline = False)
                embed.add_field(name = "Score:", value = score, inline = False)
                await ctx.response.send_message(embed)

            elif hand == "✌️":
                if bothand == "🤜":
                    embed = discord.Embed(title = "I won!", description = "The bot won this one", color = discord.Colour.orange())
                    embed.add_field(name = "You chose:", value = hand, inline = False)
                    embed.add_field(name = "I chose:", value = bothand, inline = False)
                    await ctx.response.send_message(embed = embed)
                if bothand == "✋":
                    embed = discord.Embed(title = "You won!", description = "Let them AIs know who's the boss", color = discord.Colour.orange())
                    embed.add_field(name = "You chose:", value = hand, inline = False)
                    embed.add_field(name = "I chose:", value = bothand, inline = False)
                    score += 1
                    embed.add_field(name = "Score:", value = score, inline = False)
                    cursor.execute("UPDATE rps SET score = ? WHERE guild_id = ? AND user_id = ?", (score, ctx.guild.id, ctx.user.id))
                    database.commit()
                    await ctx.response.send_message(embed = embed)

            elif hand == "✋":
                if bothand == "✌️":
                    embed = discord.Embed(title = "I won!", description = "The bot won this one", color = discord.Colour.orange())
                    embed.add_field(name = "You chose:", value = hand, inline = False)
                    embed.add_field(name = "I chose:", value = bothand, inline = False)
                    await ctx.response.send_message(embed = embed)
                if bothand == "🤜":
                    embed = discord.Embed(title = "You won!", description = "Let them AIs know who's the boss", color = discord.Colour.orange())
                    embed.add_field(name = "You chose:", value = hand, inline = False)
                    embed.add_field(name = "I chose:", value = bothand, inline = False)
                    score += 1
                    embed.add_field(name = "Score:", value = score, inline = False)
                    cursor.execute("UPDATE rps SET score = ? WHERE guild_id = ? AND user_id = ?", (score, ctx.guild.id, ctx.user.id))
                    database.commit()
                    await ctx.response.send_message(embed = embed)      

            elif hand == "🤜":
                if bothand == "✋":
                    embed = discord.Embed(title = "I won!", description = "The bot won this one", color = discord.Colour.orange())
                    embed.add_field(name = "You chose:", value = hand, inline = False)
                    embed.add_field(name = "I chose:", value = bothand, inline = False)
                    await ctx.response.send_message(embed = embed)

                if bothand == "✌️":
                    embed = discord.Embed(title = "You won!", description = "Let them AIs know who's the boss", color = discord.Colour.orange())
                    embed.add_field(name = "You chose:", value = hand, inline = False)
                    embed.add_field(name = "I chose:", value = bothand, inline = False)
                    score += 1
                    embed.add_field(name = "Score:", value = score, inline = False)
                    cursor.execute("UPDATE rps SET score = ? WHERE guild_id = ? AND user_id = ?", (score, ctx.guild.id, ctx.user.id))
                    database.commit()
                    await ctx.response.send_message(embed = embed)

        else: 
            await ctx.response.send_message("Please insert a valid play!")

    @app_commands.command(name="rpsstats", description="Shows your RPS Stats")
    async def rpsstats(self,ctx : discord.Interaction):
        score = cursor.execute("SELECT score FROM rps WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.user.id)).fetchone()
        if score is not None:
            score = score[0]
            embed = discord.Embed(title = "Your RPS Stats", description = "These are your RPS Stats", color = discord.Colour.orange())
            embed.add_field(name = "Score:", value = score, inline = False)
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.response.send_message("You haven't played RPS yet!")
    
    @app_commands.command(name="rpsleaderboard", description="Shows the RPS Leaderboard")
    async def rpsleaderboard(self,ctx : discord.Interaction):
        scores = cursor.execute("SELECT user_id, score FROM rps WHERE guild_id = ? ORDER BY score DESC", (ctx.guild.id,)).fetchall()
        if scores is not None:
            embed = discord.Embed(title = "RPS Leaderboard", description = "These is the RPS Leaderboard", color = discord.Colour.orange())
            for score in scores:
                user = await self.bot.fetch_user(score[0])
                embed.add_field(name = f"{user.display_name}", value = f"Score: {score[1]}", inline = False)
            await ctx.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Shows the bot's commands")
    async def help(self,ctx : discord.Interaction):
        #Fun Commands Embed
        MyEmbed = discord.Embed(title = "Fun Commands", description = "These are the bot's Fun commands", color = discord.Colour.orange())
        MyEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        MyEmbed.add_field(name = "Fun Commands", value = "Some Fun Bot Commands", inline = False)
        MyEmbed.add_field(name = "/ping", value = "The bot replies with Pong!", inline = False)
        MyEmbed.add_field(name = "/coinflip", value = "This command lets you flip a coin", inline = False)
        MyEmbed.add_field(name = "/rps ✌️/🤜/✋", value = "This comand allows to play a game of rock paper scissors with the bot", inline = False)
        MyEmbed.add_field(name = "/rpsstats", value = "This comand allows you to view your RPS Stats", inline = False)
        MyEmbed.add_field(name = "/rpsleaderboard", value = "This comand allows you to view the RPS Leaderboard", inline = False)
        MyEmbed.add_field(name = "/dice NdN", value = "This comand allows you to roll a dice in NdN format. Example: 1d6", inline = False)
        MyEmbed.add_field(name = "/rank", value = "This comand allows you to view your level!", inline = False)
        
        #Music Commands Embed
        MusicEmbed = discord.Embed(title = "Music Commands", description = "These are the Bot's Music Commands", color = discord.Colour.orange())
        MusicEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        MusicEmbed.add_field(name = "/play", value = "This command makes the bot Play a song when in a voice channel! ", inline = False)
        MusicEmbed.add_field(name = "/skip", value = "This command skips the current song!", inline = False)        #MusicEmbed.add_field(name = ".ds skip", value = "This comand skips to the queue's next song!", inline = False)
        MusicEmbed.add_field(name = "/pause", value = "This command pauses the song playing!", inline = False)
        MusicEmbed.add_field(name = "/resume", value = "This command resumes the paused song!", inline = False)
        MusicEmbed.add_field(name = "/setvolume", value = "This command sets the bot Volume (1-1000)", inline = False)
        MusicEmbed.add_field(name = "/loop", value = "This command loops the current song!", inline = False)
        MusicEmbed.add_field(name = "/disconnect", value = "This command disconnects the bot from the channel", inline = False)
        MusicEmbed.add_field(name = "/queue", value = "This command allows the user to view what songs are in queue!", inline = False)
        
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

        #Bot Config Commands
        ConfigEmbed = discord.Embed(title = "Bot Config Commands", description = "These are the Bot's Config Commands", color = discord.Colour.orange())
        ConfigEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        ConfigEmbed.add_field(name = "/config setwelcomechannel", value = "Sets the Welcome Channel!", inline = False)
        ConfigEmbed.add_field(name = "/config setlevelupchannel", value = "Sets the Level Up Channel! (Defaults to the channel where the message that triggered the level up was sent if not set)", inline = False)

        #Disclaimer Embed
        DisclaimerEmbed = discord.Embed(title = "Disclaimer", description = "About the leveling system", color = discord.Colour.orange())
        DisclaimerEmbed.set_thumbnail(url = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg")
        DisclaimerEmbed.add_field(name = "Disclaimer", value = 'There are 4 level tiers where you can "lock" certain premissions Lvl 5, 10, 20 and 30. This bot creates roles for each tier, however you will have to manualy configure and customize them while the developer finds a better way to do it through commands or an online interface.', inline = False)

        
        #DM Creation
        await ctx.response.send_message("Check your DMs!")
        await ctx.user.create_dm()
        await ctx.user.dm_channel.send(embed = MyEmbed)
        await ctx.user.dm_channel.send(embed = MusicEmbed) 
        await ctx.user.dm_channel.send(embed = ModEmbed)
        await ctx.user.dm_channel.send(embed = ConfigEmbed)   
        await ctx.user.dm_channel.send(embed = DisclaimerEmbed)

    #----------------------------------------------//----------------------------------------------#
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
        await ctx.response.defer()
        if amount == "/":
            if day == None or month == None:
                return
            else:
                await ctx.channel.purge(after = datetime(year, month, day))
                await ctx.channel.send(f"Deleted all messages after {day}/{month}/{year}")
        else:
            await ctx.channel.purge(limit = int(amount) + 1)
            await ctx.channel.send(f"Deleted {amount} messages")

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
    #Bot Config Commands

    config = app_commands.Group(name="config", description="Bot Config Commands")

    @config.command(name="setwelcomechannel", description="Sets the Welcome Channel")
    @app_commands.describe(channel = "The channel to set as the Welcome Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setwelcomechannel(self,ctx : discord.Interaction, channel : discord.TextChannel):
        cursor.execute("SELECT * FROM welcome WHERE guild_id = ?", (ctx.guild.id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO welcome VALUES (?,?)", (ctx.guild.id, channel.id))
            database.commit()
        else:
            cursor.execute("UPDATE welcome SET welcome_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
            database.commit()
        await ctx.response.send_message(f"Welcome Channel set to {channel.mention}")

    @config.command(name="setlevelupchannel", description="Sets the Level Up Channel")
    @app_commands.describe(channel = "The channel to set as the Level Up Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setwelcomechannel(self,ctx : discord.Interaction, channel : discord.TextChannel):
        cursor.execute("SELECT * FROM levelup WHERE guild_id = ?", (ctx.guild.id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO levelup VALUES (?,?)", (ctx.guild.id, channel.id))
            database.commit()
        else:
            cursor.execute("UPDATE levelup SET levelup_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
            database.commit()
        await ctx.response.send_message(f"Level Up Channel set to {channel.mention}")

    @config.command(name="settwitchnotificationchannel", description="Sets the Channel for Twitch Notifications")
    @app_commands.describe(channel = "The channel to set as the Notification Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setwelcomechannel(self,ctx : discord.Interaction, channel : discord.TextChannel):
        cursor.execute("SELECT * FROM twitch_config WHERE guild_id = ?", (ctx.guild.id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO twitch_config VALUES (?,?)", (ctx.guild.id, channel.id))
            database.commit()
        else:
            cursor.execute("UPDATE twitch_config SET welcome_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
            database.commit()
        await ctx.response.send_message(f"Notification Channel set to {channel.mention}")

    @config.command(name="addstreamer", description="Adds a Streamer for Twitch Notifications")
    @app_commands.describe(streamer = "The streamer to add")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def addStreamer(self,ctx : discord.Interaction, streamer : str):
        notChannel = cursor.execute("SELECT twitch_channel_id FROM twitch_config WHERE guild_id = ?", (ctx.guild.id,)).fetchone()

        if notChannel[0] is None:
            await ctx.response.send_message("Please set a Notification Channel first!")
        else:
            cursor.execute("INSERT INTO twitch VALUES (?,?)", (streamer, ctx.guild.id))
            database.commit()
            await ctx.response.send_message(f"Added {streamer} to the Streamers List!")

    #----------------------------------------------//----------------------------------------------#
    #Error Handlers

    #Moderation Commands ErrorHandlers
    @servername.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @region.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
        if isinstance(error, app_commands.errors.CommandInvokeError):
            await ctx.response.send_message("Please choose a valid region!")

    @createtextchannel.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @createvoicechannel.error
    async def errorhandler(self, ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @kick.error
    async def errorhandler(self,ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

    @ban.error
    async def errorhandler(self,ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")
    @purge.error
    async def errorhandler(self,ctx : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await ctx.response.send_message("You don't have permission to do that!")

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
    
async def setup(bot) -> None:
    await bot.add_cog(CommandHandler(bot))