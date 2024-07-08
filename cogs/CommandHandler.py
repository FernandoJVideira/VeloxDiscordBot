import re
import discord
from discord import app_commands
from discord.app_commands import Choice
import random
from datetime import datetime
from discord.ext import commands
import sqlite3
from easy_pil import Canvas, Font, Editor, load_image_async

DATABASE = "bot.db"
LEVELSYS_QUERY = "SELECT levelsys FROM levelsettings WHERE guild_id = ?"
LVLSYS_DISABLED = "The Leveling System is disabled in this server!"
LVLSYS_INSERT_QUERY = "INSERT INTO levelsettings VALUES (?,?,?,?,?)"
NO_PERMS_MESSAGE = "You don't have permission to do that!"
EMBED_IMAGE = "https://i.pinimg.com/originals/40/b4/69/40b469afa11db730d3b9ffd57e9a3af9.jpg"

database = sqlite3.connect(DATABASE)
cursor = database.cursor()
class CommandHandler(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #* Fun Commands
    #* Ping Command, replies with Pong! and the latency of the bot
    @app_commands.command(name="ping", description="Pings the bot")
    async def ping(self, interaction : discord.Interaction):
        await interaction.response.send_message(f"Pong! 🏓  {self.bot.latency * 1000:.0f}ms")

    #* Sends a message with a coinflip
    @app_commands.command(name="coinflip", description="Flips a coin")
    async def coinflip(self,interaction : discord.Interaction):
        #* Generates a random number between 1 and 2
        num = random.randint(1, 2)
        #* If the number is 1, send Heads!, if it's 2, send Tails!
        if num == 1:
            await interaction.response.send_message("Heads!")
        if num == 2:
            await interaction.response.send_message("Tails!")

    @app_commands.command(name="dice", description="Rolls a dice")
    async def dice(self,interaction : discord.Interaction, dice: str):
        pattern_index = self.matches_template(dice.content)
        if pattern_index is not None:
            match pattern_index:
                case 1 | 0:
                    text = await self.sum_rolled_dice(dice)
                    await interaction.response.send_message(text)                  
                case 2:
                    num_dice, dice_type, modifier, modifier_line = self.parse_separate_dice(dice) 
                    messages = await self.roll_multiple_dice(num_dice, dice_type, modifier, modifier_line)
                    await interaction.response.send_message('\n'.join(messages))



    #* Sends an image with the user's current rank
    @app_commands.command(name= "rank", description="Shows your level!")
    async def rank(self, interaction : discord.Interaction, member: discord.Member = None):
        #*If no member is specified, use the user
        if member is None:
            member = interaction.user

        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (interaction.guild.id,))


        if levelsys and levelsys[0] and not levelsys[0][0]:
            await interaction.response.send_message(LVLSYS_DISABLED)
            return
        
        xp, level = await self.getLvlAndXp(member, interaction.guild)

        user_data = {
            "name" : member.display_name,
            "xp" : xp,
            "level" : level,
            "nextLevelXp" : 100,
            "precentage" : xp
        }

        file = await self.createRankImage(member, user_data)
        await interaction.response.send_message(file=file)

    #*Sends a message with the rewards for each level
    @app_commands.command(name="rewards", description="Lets you see the rewards for each level")
    async def rewards(self, interaction : discord.Interaction):
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (interaction.guild.id,))

        if levelsys and levelsys[0] and not levelsys[0][0]:
            await interaction.response.send_message(LVLSYS_DISABLED)
            return
        
        #* Fetch role rewards
        role_rewards_query = "SELECT * FROM levelsettings WHERE guild_id = ?"
        role_rewards = self.fetch_from_db(role_rewards_query, (interaction.guild.id,))
        role_rewards = role_rewards[1:]

        #* If there are no rewards, send a message
        if not role_rewards:
            await interaction.response.send_message("There are no rewards set for this server!")
            return
        #* Create embed for role rewards
        em = await self.createRoleRewardsEmbrd(interaction, role_rewards)

        await interaction.response.send_message(embed=em)

    #* Sends a message with the guild's level leaderboard
    @app_commands.command(name="leaderboard", description="Displays the server's leaderboard")
    async def leaderboard(self, interaction : discord.Interaction):
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (interaction.guild.id,))

        if levelsys and levelsys[0] and not levelsys[0][0]:
            await interaction.response.send_message(LVLSYS_DISABLED)
            return
        
        #* Fetch leaderboard data
        data_query = "SELECT level, xp, user FROM levels WHERE guild = ? ORDER BY level DESC, xp DESC LIMIT 10"
        data = self.fetch_from_db(data_query, (interaction.guild.id,))

        #*If there's data, create the embed and send it
        if data:
            em = await self.createLevelLeaderBoardEmbed(data, interaction)
            await interaction.response.send_message(embed=em)
            return

        return await interaction.response.send_message("There are no users in the leaderboard!")

    #* Plays Rock Paper Scissors with the user
    @app_commands.command(name="rps", description="Plays Rock Paper Scissors with you")
    @app_commands.describe(hand = "Choose between ✌️, ✋ or 🤜")
    @app_commands.choices(hand = [
        Choice(name = "✌️ - Scissors", value = "✌️"),
        Choice(name = "✋ - Paper", value = "✋"),
        Choice(name = "🤜 - Rock", value = "🤜"),
        ])
    async def rps(self,interaction : discord.Interaction, hand : str):
        #* Sets the valid choices and randomly picks the bot's hand
        hands = ["✌️", "✋", "🤜"]
        bot_hand = random.choice(hands)
        #* Verifies if the user's choice is valid
        if hand not in hands:
            return
        #* Gets the user's score 
        score = self.get_score(interaction)
        #* If the user wins the returned color is green, otherwise it's red
        #* The result is the game result
        result, color = self.determine_game_result(hand, bot_hand)
        #* Updates the user's score
        if result == "You won!":
            score = (score[0] + 1,)
            query = "UPDATE rps SET score = ? WHERE guild_id = ? AND user_id = ?"
            self.execute_db_query(query, (score[0], interaction.guild.id, interaction.user.id))
        #* Sends the game result
        await self.send_game_result(interaction, result, hand, bot_hand, score, color)

    #* Shows the user's RPS Stats
    @app_commands.command(name="rpsstats", description="Shows your RPS Stats")
    async def rpsstats(self, interaction: discord.Interaction):
        #* Fetch user's score
        user_score_query = "SELECT score FROM rps WHERE guild_id = ? AND user_id = ?"
        user_score = self.fetch_from_db(user_score_query, (interaction.guild.id, interaction.user.id))

        #* If the user has played RPS, create the embed and send it
        if user_score is not None:
            user_score = user_score[0]
            embed = await self.create_score_embed(user_score)
            await interaction.response.send_message(embed=embed)
        else:
            #* If the user hasn't played RPS, send a message
            await interaction.response.send_message("You haven't played RPS yet!")
    
    @app_commands.command(name="rpsleaderboard", description="Shows the RPS Leaderboard")
    async def rpsleaderboard(self, interaction: discord.Interaction):
        #* Fetch leaderboard scores
        leaderboard_query = "SELECT user_id, score FROM rps WHERE guild_id = ? ORDER BY score DESC"
        leaderboard_scores = self.fetch_from_db(leaderboard_query, (interaction.guild.id,))
        
        #* If there's data, create the embed and send it
        if leaderboard_scores is not None:
            embed = await self.create_leaderboard_embed(leaderboard_scores)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Shows the bot's commands")
    @app_commands.describe(option = "The command to get help with")
    @app_commands.choices(option = [
        Choice(name = "Fun Commands", value = "fun"),
        Choice(name = "Music", value = "music"),
        Choice(name = "Config", value = "config"),
        Choice(name = "Moderation", value = "moderation"),
        Choice(name = "Leveling", value = "levelingsys")
    ])

    async def help(self,interaction : discord.Interaction, option : str = None):
        embeds = []

        match option:
            case None:
                fun_embed = await self.createFunCmdEmbed()
                music_embed = await self.createMusicCmdEmbed()
                mod_embed = await self.createAdminCmdEmbed()
                config_embed = await self.createConfigCmdEmbed()
                leveling_embed = await self.createLevelingEmbed()
                embeds.extend([fun_embed, music_embed, mod_embed, config_embed, leveling_embed])
            case "fun":
                fun_embed = await self.createFunCmdEmbed()
                embeds.append(fun_embed)
            case "music":
                music_embed = await self.createMusicCmdEmbed()
                embeds.append(music_embed)
            case "config":
                config_embed = await self.createConfigCmdEmbed()
                embeds.append(config_embed)
            case "moderation":
                mod_embed = await self.createAdminCmdEmbed()
                embeds.append(mod_embed)
            case "levelingsys":
                leveling_embed = await self.createLevelingEmbed()
                embeds.append(leveling_embed)

        #* Creates the dm channel and sends the embeds
        await interaction.response.send_message("Check your DMs!")
        await interaction.user.create_dm()
        for em in embeds:
            await interaction.user.dm_channel.send(embed = em)


    #----------------------------------------------//----------------------------------------------#
    #Group Command EditSever
    """This group of commands allows the user to edit the server settings"""
    serverGroup = app_commands.Group(name = "editserver", description="Edit Server Settings")

    @serverGroup.command(name="servername", description="Edits the Server Name")
    @app_commands.describe(input = "The new Server Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def servername(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.edit(name = input)
        await interaction.response.send_message(f"Server Name Changed to {input}")

    @serverGroup.command(name="region", description="Edits the Server Region")
    @app_commands.describe(input = "The new Server Region")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def region(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.edit(region = input)
        await interaction.response.send_message(f"Server Region Changed to {input}")

    @serverGroup.command(name="createtextchannel", description="Creates a Text Channel")
    @app_commands.describe(input = "The new Text Channel Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createtextchannel(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.create_text_channel(name = input)
        await interaction.response.send_message(f"Text Channel Created with the name {input}")

    @serverGroup.command(name="createvoicechannel", description="Creates a Voice Channel")
    @app_commands.describe(input = "The new Voice Channel Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createvoicechannel(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.create_voice_channel(name = input)
        await interaction.response.send_message(f"Voice Channel Created with the name {input}")

    @serverGroup.command(name="createrole", description="Creates a Role")
    @app_commands.describe(input = "The new Role Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createrole(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.create_role(name = input)
        await interaction.response.send_message(f"Role Created with the name {input}")

    #*----------------------------------------------//----------------------------------------------*#
    #* Moderation Commands  
    """This group of commands allows the user to moderate the server"""
    moderationGroup = app_commands.Group(name= "moderation", description="Moderation Commands")

    @moderationGroup.command(name="kick", description="Kicks a user")
    @app_commands.describe(member = "The user to kick")
    @app_commands.checks.has_permissions(kick_members = True)
    async def kick(self,interaction : discord.Interaction, member : discord.Member, *, reason : str):
        await interaction.guild.kick(member, reason = reason)
        await interaction.response.send_message(f"Kicked {member}")

    @moderationGroup.command(name="ban", description="Bans a user")
    @app_commands.describe(member = "The user to ban", reason = "The reason for the ban")
    @app_commands.checks.has_permissions(ban_members = True)
    async def ban(self,interaction : discord.Interaction, member : discord.Member, *, reason : str):
        await interaction.guild.ban(member, reason = reason)
        await interaction.response.send_message(f"Banned {member}")

    @moderationGroup.command(name="unban", description="Unbans a user")
    @app_commands.describe(user_to_unban = "User to unban")
    @app_commands.checks.has_permissions(ban_members = True)
    async def unban(self, interaction: discord.Interaction, *, user_to_unban: str):
        banned_members = await interaction.guild.bans()
        user = self.find_banned_user(banned_members, user_to_unban)

        if user is not None:
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"Unbanned {user.name}")
                
    @moderationGroup.command(name="purge", description="Clears X amount of messages from a channel")
    @app_commands.describe(message_limit_or_date_indicator = "The amount of messages to delete", day = "The day to delete from", month = "The month to delete from", year = "The year to delete from")
    @app_commands.checks.has_permissions(manage_messages = True)
    async def purge(self, interaction: discord.Interaction, message_limit_or_date_indicator: int, day: int = None, month: int = None, year: int = datetime.now().year):
        if str(message_limit_or_date_indicator) == "/":
            if day is None or month is None:
                return
            else:
                await interaction.response.send_message(f"Purging messages from {day}/{month}/{year}")
                await self.purge_messages_by_date(interaction, day, month, year)
        else:
            await interaction.response.send_message(f"Purging {message_limit_or_date_indicator} messages")
            await self.purge_messages_by_limit(interaction, message_limit_or_date_indicator)

    @moderationGroup.command(name="mute", description="Mutes a user")
    @app_commands.describe(user = "The user to mute")
    @app_commands.checks.has_permissions(mute_members = True)
    async def mute(self, interaction : discord.Interaction, user : discord.Member):
        await user.edit(mute = True)
        await interaction.response.send_message(f"Muted {user}")

    @moderationGroup.command(name="unmute", description="Unmutes a user")
    @app_commands.describe(user = "The user to unmute")
    @app_commands.checks.has_permissions(mute_members = True)
    async def unmute(self,interaction : discord.Interaction, user : discord.Member ):
        await user.edit(mute = False)
        await interaction.response.send_message(f"Unmuted {user}")

    @moderationGroup.command(name="deafen", description="Deafens a user")
    @app_commands.describe(user = "The user to deafen")
    @app_commands.checks.has_permissions(deafen_members = True)
    async def deafen(self,interaction : discord.Interaction, user : discord.Member):
        await user.edit(deafen = True)
        await interaction.response.send_message(f"Deafened {user}")

    @moderationGroup.command(name="undeafen", description="Undeafens a user")
    @app_commands.describe(user = "The user to undeafen")
    @app_commands.checks.has_permissions(deafen_members = True)
    async def undeafen(self,interaction : discord.Interaction, user : discord.Member):
        await user.edit(deafen = False)
        await interaction.response.send_message(f"Undeafened {user}")

    @moderationGroup.command(name="voicekick", description="Kicks a user from a Voice Channel")
    @app_commands.describe(user = "The user to kick from the Voice Channel")
    @app_commands.checks.has_permissions(kick_members = True)
    async def voicekick(self,interaction : discord.Interaction, user : discord.Member):
        await user.edit(voice_channel = None)
        await interaction.response.send_message(f"Kicked {user} from Voice Channel")


    #*----------------------------------------------//----------------------------------------------*#
    #* Bot Config Commands
    """This group of commands allows the user to configure the bot"""
    config = app_commands.Group(name="config", description="Bot Config Commands")

    @config.command(name="setwelcomechannel", description="Sets the Welcome Channel")
    @app_commands.describe(welcome_channel = "The channel to set as the Welcome Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setwelcomechannel(self, interaction: discord.Interaction, welcome_channel: discord.TextChannel):
        #* Gets the guild id and the channel id
        guild_id = interaction.guild.id
        channel_id = welcome_channel.id

        query = "UPDATE welcome SET welcome_channel_id = ? WHERE guild_id = ?"
        self.execute_db_query(query, (channel_id, guild_id))

        await interaction.response.send_message(f"Welcome Channel set to {welcome_channel.mention}")

    @config.command(name="removewelcomechannel", description="Removes the Channel set for Welcome Messages")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeWelcomeChannel(self,interaction : discord.Interaction):
        #* Deletes the welcome channel from the database
        query = "DELETE FROM welcome WHERE guild_id = ?"
        self.execute_db_query(query, (interaction.guild.id,))
        #* Sends a message
        await interaction.response.send_message("Removed the Welcome Channel!")

    @config.command(name="updatewelcomemessage", description="Updates the Default Welcome Embed Message")
    @app_commands.describe(message = "The new Welcome Message")
    async def updateWelcomeMessage(self,interaction : discord.Interaction, *, message : str):
        query = "UPDATE welcome SET welcome_message = ? WHERE guild_id = ?"
        self.execute_db_query(query, (message, interaction.guild.id))
        await interaction.response.send_message("Welcome Message Updated!")

    @config.command(name="updatewelcomedm", description="Updates the Default Welcome DM Message")
    @app_commands.describe(message = "The new Welcome DM Message")
    async def updateWelcomeDmMessage(self,interaction : discord.Interaction, *, message : str):
        query = "UPDATE welcome SET welcome_dm = ? WHERE guild_id = ?"
        self.execute_db_query(query, (message, interaction.guild.id))
        await interaction.response.send_message("Welcome Message DM Updated!")

    @config.command(name="updatewelcomegif", description="Updates the Default Welcome Embed Gif")
    @app_commands.describe(url = "The new Welcome Gif URL")
    async def updateWelcomeGif(self,interaction : discord.Interaction, *, url : str):
        query = "UPDATE welcome SET welcome_gif_url = ? WHERE guild_id = ?"
        self.execute_db_query(query, (url, interaction.guild.id))
        await interaction.response.send_message("Welcome Embed Gif Updated!")


    @config.command(name="setlevelupchannel", description="Sets the Level Up Channel")
    @app_commands.describe(levelup_channel = "The channel to set as the Level Up Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setLevelUpChannel(self, command_context: discord.Interaction, levelup_channel: discord.TextChannel):
        #* Gets the guild id and the channel id
        guild_id = command_context.guild.id
        channel_id = levelup_channel.id
        #* Fetches the existing levelup channel, if there is one
        channel_query = "SELECT levelup_channel_id FROM levelup WHERE guild_id = ?"
        existing_levelup_channel = self.fetch_from_db(channel_query, (guild_id,))
        #* If there's no levelup channel, insert it into the database, otherwise update it
        if not existing_levelup_channel:
            query = "INSERT INTO levelup VALUES (?,?)"
            self.execute_db_query(query, (guild_id, channel_id))
        else:
            query = "UPDATE levelup SET levelup_channel_id = ? WHERE guild_id = ?"
            self.execute_db_query(query, (guild_id, channel_id))
        #* Sends a message
        await command_context.response.send_message(f"Level Up Channel set to {levelup_channel.mention}")

    @config.command(name="removelevelupchannel", description="Removes the Channel set for Level Up Notifications")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeStreamChannel(self,interaction : discord.Interaction):
        #* Deletes the levelup channel from the database
        cursor.execute("DELETE FROM levelup WHERE guild_id = ?", (interaction.guild.id,))
        database.commit()
        #* Sends a message
        await interaction.response.send_message("Removed the Level Up Channel!")

    @config.command(name="settwitchnotificationchannel", description="Sets the Channel for Twitch Notifications")
    @app_commands.describe(twitch_notification_channel = "The channel to set as the Notification Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setTwitchNotificationChannel(self, command_context: discord.Interaction, twitch_notification_channel: discord.TextChannel):
        #* Gets the guild id and the channel id
        guild_id = command_context.guild.id
        channel_id = twitch_notification_channel.id
        #* Fetches the existing twitch channel, if there is one
        config_query = "SELECT twitch_channel_id FROM twitch_config WHERE guild_id = ?"
        existing_twitch_config = self.fetch_from_db(config_query, (guild_id,))
        #* If there's no twitch channel, insert it into the database, otherwise update it
        if not existing_twitch_config:
            query = "INSERT INTO twitch_config VALUES (?,?)"
            self.execute_db_query(query, (guild_id, channel_id))
        else:
            query = "UPDATE twitch_config SET twitch_channel_id = ? WHERE guild_id = ?"
            self.execute_db_query(query, (guild_id, channel_id))
        #* Sends a message
        await command_context.response.send_message(f"Notification Channel set to {twitch_notification_channel.mention}")
    
    @config.command(name="removestreamchannel", description="Removes the Channel set for Twitch Notifications")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeStreamChannel(self,interaction : discord.Interaction):
        #* Deletes the twitch channel from the database
        query = "DELETE FROM twitch_config WHERE guild_id = ?"
        self.execute_db_query(query, (interaction.guild.id,))
        #* Sends a message
        await interaction.response.send_message("Removed the Notification Channel!")

    @config.command(name="addstreamer", description="Adds a Streamer for Twitch Notifications")
    @app_commands.describe(streamer = "The streamer to add")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def addStreamer(self,interaction : discord.Interaction, streamer : str):
        #* Fetches the existing twitch channel, if there is one
        not_channel_querry = "SELECT twitch_channel_id FROM twitch_config WHERE guild_id = ?"
        not_channel = self.fetch_from_db(not_channel_querry, (interaction.guild.id,))
        #* If there's no twitch channel, send a message, otherwise add the streamer to the database
        if not not_channel:
            await interaction.response.send_message("Please set a Notification Channel first!")
        else:
                streamer = self.checkStreamer(streamer)
                if len(streamer) > 0:
                    await interaction.response.send_message("This streamer is already in the Streamers List!")
                    return
                
                query = "INSERT INTO twitch VALUES (?,?,?)"
                self.execute_db_query(query, (streamer,"not live", interaction.guild.id))
                await interaction.response.send_message(f"Added {streamer} to the Streamers List!")

    @config.command(name="removestreamer", description="Removes a Streamer from Twitch Notifications")
    @app_commands.describe(streamer = "The streamer to remove")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeStreamer(self,interaction : discord.Interaction, streamer : str):

        if await self.checkStreamer(streamer) is None:
            await interaction.response.send_message("This streamer is not in the Streamers List!")
            return
        #* Deletes the streamer from the database
        query = "DELETE FROM twitch WHERE twitch_user = ? AND guild_id = ?"
        self.execute_db_query(query, (streamer, interaction.guild.id))
        #* Sends a message
        await interaction.response.send_message(f"Removed {streamer} from the Streamers List!")      

    @config.command(name="setdefaultrole", description="Sets the Default Role when a user joins the server")
    @app_commands.describe(default_role = "The role to set as the Default Role")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setDefaultRole(self, command_context: discord.Interaction, default_role: discord.Role):
        #* Gets the guild id and the role id
        guild_id = command_context.guild.id
        role_id = default_role.id
        #* Fetches the existing default role, if there is one
        existing_default_role = self.fetch_from_db("SELECT * FROM defaultrole WHERE guild_id = ?", (guild_id,))
        #* If there's no default role, insert it into the database, otherwise update it
        if not existing_default_role:
            query = "INSERT INTO defaultrole VALUES (?,?)"
            self.execute_db_query(query, (guild_id, role_id))
        else:
            query = "UPDATE defaultrole SET role_id = ? WHERE guild_id = ?"
            self.execute_db_query(query, (role_id, guild_id))
        #* Sends a message
        await command_context.response.send_message(f"Default Role set to {default_role.mention}")  

    """This group of commands allows the user to configure the Server Leveling System"""
    slvl = app_commands.Group(name="slvl", description="Configure the Server Leveling System")

    @slvl.command(name="enable", description="Enables the Server Leveling System")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def enable(self, command_context: discord.Interaction):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Fetches the existing levelsys, if there is one
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (guild_id,))

        #* If there's no levelsys, insert it into the database, otherwise update it
        if not levelsys:
            query = LVLSYS_INSERT_QUERY
            self.execute_db_query(query, (True, 0, 0, None, guild_id))
        else:
            #*If the levelsys is already enabled, send a message 
            if levelsys[0] and levelsys[0][0]:
                await command_context.response.send_message("The Leveling System is already enabled!")
                return
            query = "UPDATE levelsettings SET levelsys = ? WHERE guild_id = ?"
            self.execute_db_query(query, (True, guild_id))
        #* Sends a message
        await command_context.response.send_message("Leveling System Enabled!")

    @slvl.command(name="disable", description="Disables the Server Leveling System")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def disable(self,interaction : discord.Interaction):
        #* Gets the guild id
        guild_id = interaction.guild.id
        #* Fetches the existing levelsys, if there is one
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (guild_id,))

        #* If there's no levelsys, insert it into the database, otherwise update it
        if not levelsys:
            query = LVLSYS_INSERT_QUERY
            self.execute_db_query(query, (False, 0, 0, None, guild_id))
        else:
            #* If the levelsys is already enabled, send a message
            if levelsys and levelsys[0] and not levelsys[0][0]:
                await interaction.response.send_message("The Leveling System is already disabled!")
                return
            query = "UPDATE levelsettings SET levelsys = ? WHERE guild_id = ?"
            self.execute_db_query(query, (guild_id, False))
        #* Sends a message
        await interaction.response.send_message("Leveling System Disabled!")

    @slvl.command(name="setlevelrewards", description="Sets the Level Rewards")
    @app_commands.describe(reward_level = "The level to set the reward for", reward_role = "The role to give as a reward")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setrole(self, command_context: discord.Interaction, reward_level: int, *, reward_role: discord.Role):
        #* Gets the guild id and the role id
        guild_id = command_context.guild.id
        role_id = reward_role.id

        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (guild_id,))

        if levelsys and levelsys[0] and not levelsys[0][0]:
            await command_context.response.send_message(LVLSYS_DISABLED)
            return
        
        #* Fetches the existing reward role, if there is one
        role_tf_query = "SELECT role FROM levelsettings WHERE role = ? AND guild_id = ?"
        role_tf = self.fetch_from_db(role_tf_query, (role_id, guild_id))
        level_tf_query = "SELECT role FROM levelsettings WHERE levelreq = ? AND guild_id = ?"
        level_tf = self.fetch_from_db(level_tf_query, (reward_level, guild_id))

        #* If there's no reward role, insert it into the database, otherwise update it
        if role_tf and level_tf:
            await command_context.response.send_message("This role is already set as a reward for this level!")
            return
        
        #* If there's no reward role, insert it into the database, otherwise update it
        query = "INSERT INTO levelsettings VALUES (?,?,?,?)"
        self.execute_db_query(query, (True, role_id, reward_level, None, guild_id))
        await command_context.response.send_message(f"Set {reward_role.mention} as a reward for level {reward_level}!")
    
    @slvl.command(name="removereward", description="Removes a Level Reward")
    @app_commands.describe(reward_level = "The level to remove the reward from")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removereward(self, command_context: discord.Interaction, reward_level: int):
        #* Gets the guild id
        guild_id = command_context.guild.id

        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, guild_id,)

        if levelsys and levelsys[0] and not levelsys[0][0]:
            await command_context.response.send_message(LVLSYS_DISABLED)
            return

        #* Fetches the existing reward role, if there is one
        query = "DELETE FROM levelsettings WHERE levelreq = ? AND guild_id = ?"
        self.execute_db_query(query, (reward_level, guild_id))
        await command_context.response.send_message(f"Removed the reward for level {reward_level}!")

    @slvl.command(name="setlvlupmessage", description="Sets the Level Up Message")
    @app_commands.describe(level_up_message = " {user} is the user that leveled up and {level} is the level the user leveled up to")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setlvlupmessage(self, command_context: discord.Interaction, *, level_up_message: str):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (guild_id,))
        #* If the leveling system is disabled, send a message
        if levelsys is None or not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED)
            return

        #* Fetches the existing level up message, if there is one
        level_up_message_query = "SELECT message FROM levelsettings WHERE guild_id = ?"
        lvlupmessage = self.fetch_from_db(level_up_message_query, (guild_id,))

        #* If there's no level up message, insert it into the database, otherwise update it
        if lvlupmessage:
            query = "UPDATE levelsettings SET message = ? WHERE guild_id = ?"
            self.execute_db_query(query, (level_up_message, guild_id))
        else:
            query = LVLSYS_INSERT_QUERY
            self.execute_db_query(query, (True, 0, 0, level_up_message, guild_id))
            self.insert_message(guild_id, level_up_message)

        #* Sends a message
        await command_context.response.send_message("Level Up Message set!")
    
    @slvl.command(name="resetlvlupmessage", description="Resets the Level Up Message")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def resetlvlupmessage(self, command_context: discord.Interaction):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (guild_id,))
        #* If the leveling system is disabled, send a message
        if levelsys is None or not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED)
            return
        #* Resets the level up message
        query = "UPDATE levelsettings SET message = ? WHERE guild_id = ?"
        self.execute_db_query(query, (None, guild_id))
        await command_context.response.send_message("Level Up Message reset!")

    @slvl.command(name="setlvl", description="Sets the User's Level")
    @app_commands.describe(user = "The user to set the level for", level = "The level to set")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setlvl(self, command_context: discord.Interaction, user: discord.Member, level: int):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.fetch_from_db(levelsys_query, (guild_id,))
        #* If the leveling system is disabled, send a message
        if levelsys and levelsys[0] and not levelsys[0][0]:
            await command_context.response.send_message(LVLSYS_DISABLED)
            return
        #* Fetches the existing level, if there is one
        level_query = "SELECT level FROM levels WHERE user = ? AND guild = ?"
        existing_level = self.fetch_from_db(level_query, (user.id, guild_id))
        #* If there's no level, insert it into the database, otherwise update it
        if existing_level:
            #Set the level to the new level and xp 0
            query = "UPDATE levels SET level = ?, xp = ? WHERE user = ? AND guild = ?"
            self.execute_db_query(query, (level, 0, user.id, guild_id))
        else:
            query = "INSERT INTO levels VALUES (?,?,?,?)"
            self.execute_db_query(query, (level, 0, user.id, guild_id))
        #* Sends a message
        await command_context.response.send_message(f"Set {user.mention}'s level to {level}!")


    #*----------------------------------------------//----------------------------------------------#
    #* These functions are used by the commands in case of an error
    #* They simply send a message to the user acording to the error

    @scream.error
    async def scream_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await interaction.response.send_message("You must have the Panik role to use this command.")

    #Moderation Commands ErrorHandlers
    @servername.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @region.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)
        if isinstance(error, app_commands.errors.CommandInvokeError):
            await interaction.response.send_message("Please choose a valid region!")

    @createtextchannel.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @createvoicechannel.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @kick.error
    async def errorhandler(self,interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @ban.error
    async def errorhandler(self,interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)
    @purge.error
    async def errorhandler(self,interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @deafen.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @undeafen.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @mute.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @unmute.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    @voicekick.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)
    
    @unban.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE)

    #*Utility Functions

    async def checkStreamer(self, streamer):
        #* Fetches the streamer from the database
        query = "SELECT * FROM twitch WHERE twitch_user = ?"
        return self.fetch_from_db(query, (streamer,))

    """
        The function `sum_rolled_dice` takes a string representing dice rolls and
        returns the total sum of the rolled dice along with the individual rolls.
        
        :param dice: The `dice` parameter in the `sum_rolled_dice` function is a
        string that represents a dice rolling expression. It can contain multiple
        parts separated by '+'. Each part can be either a simple integer or a dice
        rolling expression in the format of 'NdM', where N is the number of
        :type dice: str
        :return: The function `sum_rolled_dice` returns a formatted string that
        includes the total sum of the rolled dice and the individual rolls for each
        dice part in the input `dice` string. The format of the return string is as
        follows:
    """
    async def sum_rolled_dice(self, dice: str) -> str:
        original_dice = dice
        dice = dice.replace('-', '+-')  # Replace '-' with '+-' to keep negative modifiers intact
        parts = dice.split('+')  # Split the dice string into parts using '+' as delimiter
        total = 0
        all_rolls = []
        for part in parts:  # Iterate over the parts in steps of 2 to handle each dice roll and its sign separately
            if 'd' in part:
                rolls, roll_str, modifier = await self.roll_single_dice(part)
                sign = '-' if '-' in part else '+'  # Determine the sign based on the part itself
                total += self.calculate_dice_sum(rolls, modifier, sign)
                all_rolls.append(roll_str)
            else:
                total += int(part)
        return f'` {max(0,total)} ` ⟵ {all_rolls} {original_dice}'

    def calculate_dice_sum(self, rolls, modifier, sign):
        if modifier:
            if sign == '-':
                return sum(rolls) - modifier
            else:
                return sum(rolls) + modifier
        else:
            return sum(rolls)

    
    """
        The function `parse_dice_str` parses a string representing a dice roll into
        the number of dice, type of dice, and modifier.
        
        :param dice_str: Thank you for providing the code snippet. It looks like the
        `parse_dice_str` method is designed to parse a string representing a dice
        roll with optional modifiers
        :type dice_str: str
        :return: The `parse_dice_str` method returns a tuple containing the number
        of dice, the type of dice, and the modifier parsed from the input
        `dice_str`.
    """
    def parse_dice_str(self, dice_str: str) -> tuple:
        num_dice, dice_type = 1, 20  # Default values
        modifier = 0  # Default modifier

        parts = dice_str.replace('-', '+-').split('+')  # Split the dice string into parts

        for part in parts:
            part = part.replace(' ', '')  # Remove any spaces in the part
            if 'd' in part:
                # If the part is another dice roll, parse it separately
                part_dice_str, part_type_str = part.split('d')  # Split the part into the number of dice and the type of dice
                if part_dice_str == '':  # If the number of dice is not specified, assume it is 1
                    part_dice_str = '1'
                if part_dice_str and part_type_str:  # Check that both strings are not empty
                    part_dice, part_type = map(int, (part_dice_str, part_type_str))  # Convert the strings to integers
                    num_dice = part_dice # Set the number of dice to the parsed value if it is not empty
                    dice_type = part_type  # Assume all dice have the same type
            else:
                modifier = int(part) if part != '' else 0 # Convert the part to an integer and add it to the modifier

        return num_dice, dice_type, modifier
    
    """
        This function rolls a specified number of dice of a certain type and returns
        the individual rolls, formatted as a string, along with a modifier.
        
        :param dice_str: The `dice_str` parameter is a string that represents the
        dice roll to be performed. It typically follows the format of "NdM+X",
        where:
        :type dice_str: str
        :return: The function `roll_single_dice` returns a tuple containing three
        elements:
        1. A list of the individual dice rolls
        2. A formatted string representing all the dice rolls
        3. The modifier for the dice roll
    """
    async def roll_single_dice(self, dice_str: str):
        num_dice, dice_type, modifier = self.parse_dice_str(dice_str)
        rolls = [self.roll_dice(dice_type) for _ in range(num_dice)]
        roll_strs = [f'**{roll}**' if roll in [1, dice_type] else str(roll) for roll in rolls]
        return rolls, ", ".join(roll_strs), modifier
    

    """
        This function rolls multiple dice of a specified type, applies a modifier,
        and returns a list of messages describing each roll.
        
        :param num_dice: The `num_dice` parameter in the `roll_multiple_dice`
        function represents the number of dice that will be rolled. This parameter
        determines how many times the `roll_dice` function will be called to
        generate random numbers for the dice rolls
        :param dice_type: The `dice_type` parameter in the `roll_multiple_dice`
        function represents the type of dice being rolled. For example, if
        `dice_type` is 6, it means you are rolling a 6-sided dice (a standard
        six-sided die)
        :param modifier: The `modifier` parameter in the `roll_multiple_dice`
        function represents a value that is added to each dice roll before
        calculating the total. It can be a positive or negative integer that adjusts
        the final result of each individual dice roll
        :param modifier_line: The `modifier_line` parameter is used to provide
        additional information about the modifier being applied to the dice roll. It
        is a string that can be included in the message generated for each dice roll
        to give context to the modifier
        :return: A list of strings representing the results of rolling multiple dice
        with the specified parameters, including the total value after applying the
        modifier. Each string in the list contains the formatted result of a single
        dice roll.
    """
    async def roll_multiple_dice(self, num_dice, dice_type, modifier, modifier_line) -> list:
        messages = []
        for _ in range(num_dice):
            roll = self.roll_dice(dice_type)
            roll_str = f'**{roll}**' if roll in [1, dice_type] else str(roll)
            total = max(0, roll + modifier)
            messages.append(f'` {total} ` ⟵ [{roll_str if roll != 20 or roll != 1 else ""}] 1d{dice_type} {modifier_line}')
        return messages

    """
        The function `parse_dice_str` takes a string representing dice notation and
        parses it to extract the number of dice, type of dice, and any modifier.
        
        :param dice: The `parse_dice_str` function takes a string representing a
        dice roll in the format of "NdM±X", where N is the number of dice, M is the
        type of dice, and X is an optional modifier
        :type dice: str
        :return: The `parse_dice_str` method returns a tuple containing the
        following elements:
        1. Number of dice (num_dice)
        2. Type of dice (dice_type)
        3. Modifier value (modifier)
        4. Modifier line as a string indicating the modifier value with a plus or
        minus sign (modifier_line)
    """
    def parse_separate_dice(self, dice: str) -> tuple:
        match = re.match(r'(\d*)\s*#?d(\d+)\s*([-+]?\s*\d+)?', dice)
        num_dice = int(match.group(1)) if match.group(1) else 1
        dice_type = int(match.group(2))
        modifier_str = match.group(3)
        modifier = int(modifier_str.replace(" ", "")) if modifier_str else 0
        modifier_line = ""
        if modifier < 0:
            modifier_line = f'- {-modifier}'
        elif modifier > 0:
            modifier_line = f'+ {modifier}'
        return num_dice, dice_type, modifier, modifier_line

    """
        This Python function simulates rolling a dice with a specified number of
        sides and returns the result.
        
        :param dice_type: The `dice_type` parameter in the `roll_dice` function
        represents the type of dice being rolled. For example, if `dice_type` is 6,
        it means you are rolling a 6-sided dice (a standard six-sided die). The
        function will then return a random integer between
        :type dice_type: int
        :return: An integer value between 1 and the specified `dice_type`
        (inclusive) is being returned.
    """
    def roll_dice(self, dice_type: int) -> int:
        return random.randint(1, dice_type)

    """
    The function `matches_template` in Python checks if a message matches
    specific patterns related to dice rolling expressions.
    
    :param message: The `matches_template` method takes a message as input and
    checks if it matches any of the predefined patterns. The patterns are
    designed to match specific formats related to dice rolling in games or
    simulations
    :return: The `matches_template` method is returning the index of the pattern
    that matches the given message after removing spaces. If no pattern matches,
    it returns `None`.
    """
    def matches_template(self, message):
        patterns = [
            r"([1-9]\d*)?d[1-9]\d*((\+|\-)([1-9]\d*)?d[0-9]\d*)*",  # Matches NdN+NdN+...+NdN, NdN, and dN where N > 0
            r"([1-9]\d*)?d[1-9]\d*((\+|\-)([1-9]\d*)?d[1-9]\d*)*(\+|\-)[0-9]\d*",  # Matches NdN+NdN+...+M, NdN+M, and dN+M
            r"[1-9]\d*#d[1-9]\d*((\+|\-)[0-9]\d*)?",  # Matches N#dN and N#dN+M where N > 0
        ]
        for i, pattern in enumerate(patterns):
            if re.fullmatch(pattern, message.replace(" ", "")):
                return i
        return None

    """
        This Python function simulates rolling a dice with a specified number of
        sides and returns the result.
        
        :param dice_type: The `dice_type` parameter in the `roll_dice` function
        represents the type of dice being rolled. For example, if `dice_type` is 6,
        it means you are rolling a 6-sided dice (a standard six-sided die). The
        function will then return a random integer between
        :type dice_type: int
        :return: An integer value between 1 and the specified `dice_type`
        (inclusive) is being returned.
    """
    def roll_dice(self, dice_type: int) -> int:
        return random.randint(1, dice_type)
    
        
    """
    The above functions create embeds for different categories of commands in a Discord bot.
    :return: The functions are returning embeds, which are formatted messages that can be sent in a
    Discord server.
    """
    async def createFunCmdEmbed(self):
        em = discord.Embed(title = "Fun Commands", description = "These are the bot's Fun commands", color = discord.Colour.orange())
        em.set_thumbnail(url = EMBED_IMAGE)
        em.add_field(name = "Fun Commands", value = "Some Fun Bot Commands", inline = False)
        em.add_field(name = "/ping", value = "The bot replies with Pong!", inline = False)
        em.add_field(name = "/coinflip", value = "This command lets you flip a coin", inline = False)
        em.add_field(name = "/rps ✌️/🤜/✋", value = "This comand allows to play a game of rock paper scissors with the bot", inline = False)
        em.add_field(name = "/rpsstats", value = "This comand allows you to view your RPS Stats", inline = False)
        em.add_field(name = "/rpsleaderboard", value = "This comand allows you to view the RPS Leaderboard", inline = False)
        em.add_field(name = "/dice NdN+M", value = "This comand allows you to roll a dice in NdN+M format. Example: 1d6+3", inline = False)
        em.add_field(name = "/rank", value = "This comand allows you to view your level!", inline = False)
        em.add_field(name = "/rewards", value = "This comand allows you to view the rewards for each level", inline = False)
        em.add_field(name = "/leaderboard", value = "This comand allows you to view the server's leaderboard", inline = False)
        return em
    
    async def createMusicCmdEmbed(self):
        em = discord.Embed(title = "Music Commands", description = "These are the Bot's Music Commands", color = discord.Colour.orange())
        em.set_thumbnail(url = EMBED_IMAGE)
        em.add_field(name = "/play", value = "This command makes the bot Play a song when in a voice channel! ", inline = False)
        em.add_field(name = "/skip", value = "This command skips the current song!", inline = False)
        em.add_field(name = "/resume", value = "This command resumes the paused song!", inline = False)
        em.add_field(name = "/setvolume", value = "This command sets the bot Volume (1-1000)", inline = False)
        em.add_field(name = "/loop", value = "This command loops the current song!", inline = False)
        em.add_field(name = "/leave", value = "This command disconnects the bot from the channel", inline = False)
        em.add_field(name = "/queue", value = "This command allows the user to view what songs are in queue!", inline = False)
        return em
    
    async def createAdminCmdEmbed(self):
        em = discord.Embed(title = "Moderation/Admin Commands", description = "These are the Bot's Moderation Commands", color = discord.Colour.orange())
        em.set_thumbnail(url = EMBED_IMAGE)
        em.add_field(name = "/editserver servername", value = "Edits the server name!", inline = False)
        em.add_field(name = "/editserver region", value = "Edits the server Region!", inline = False)
        em.add_field(name = "/editserver createrole", value = "Creates a Role in the Server!", inline = False)
        em.add_field(name = "/editserver createtextchannel and /editserver createvoicechannel", value = "Creates a Text/Voice Channel in the Server", inline = False)
        em.add_field(name = "/moderation ban @user", value = "Bans a user from the server!", inline = False)
        em.add_field(name = "/moderation kick @user", value = "Kicks a user from the server!", inline = False)
        em.add_field(name = "/moderation mute @user", value = "Mutes a user!", inline = False)
        em.add_field(name = "/moderation deafen @user", value = "Deafens a user in a Voice Channel!", inline = False)
        em.add_field(name = "/moderation purge amount", value = "Clears X amount of messages from a channel!", inline = False)
        em.add_field(name = "/moderation unban user#XXXX", value = "Unbans a user from the server!", inline = False)
        em.add_field(name = "/moderation unmute/undeafen @user", value = "Unmutes/Undeafens a user in a Voice Channel!", inline = False)
        em.add_field(name = "/moderation voicekick @user", value = "Kicks a user from the Voice Channel!", inline = False)
        em.add_field(name = "/poll minutes \"question\" \"options\"", value = "This comand allows you to start a poll", inline = False)
        return em
    
    async def createConfigCmdEmbed(self):
        em = discord.Embed(title = "Bot Config Commands", description = "These are the Bot's Config Commands", color = discord.Colour.orange())
        em.set_thumbnail(url = EMBED_IMAGE)
        em.add_field(name = "/config setwelcomechannel", value = "Sets the Welcome Channel!", inline = False)
        em.add_field(name = "/config setlevelupchannel", value = "Sets the Level Up Channel! (Defaults to the channel where the message that triggered the level up was sent if not set)", inline = False)
        em.add_field(name = "/config settwitchnotificationchannel", value = "Sets the Channel for Twitch Notifications!", inline = False)
        em.add_field(name = "/config updatewelcomemessage", value = "Updates the Default Welcome Embed Message!", inline = False)
        em.add_field(name = "/config updatewelcomedm", value = "Updates the Default Welcome DM Message!", inline = False)
        em.add_field(name = "/config updatewelcomegif", value = "Updates the Default Welcome Embed Gif!", inline = False)
        em.add_field(name = "/config removewelcomechannel", value = "Removes the Channel set for Welcome Messages!", inline = False)
        em.add_field(name = "/config removestreamchannel", value = "Removes the Channel set for Twitch Notifications!", inline = False)
        em.add_field(name = "/config addstreamer", value = "Adds a Streamer for Twitch Notifications!", inline = False)
        em.add_field(name = "/config removestreamer", value = "Removes a Streamer from Twitch Notifications!", inline = False)
        em.add_field(name = "/config setdefaultrole", value = "Sets the Default Role for new members!", inline = False)
        return em

    async def createLevelingEmbed(self):
        em = discord.Embed(title = "Leveling System", description = "About the leveling system", color = discord.Colour.orange())
        em.set_thumbnail(url = EMBED_IMAGE)
        em.add_field(name = "Leveling System", value = "The leveling system is a system that allows users to gain XP and level up. The system is based on the amount of messages sent in a server. The more messages you send, the more XP you gain. The more XP you gain, the higher your level will be. The leveling system is disabled by default, however you can enable it by using the /slvl enable command. You can also configure the leveling system by using the /slvl command.", inline = False)
        em.add_field(name = "Leveling System Commands", value = "These are the commands for the leveling system", inline = False)
        em.add_field(name = "/slvl enable/disable", value = "Enables/Disables the leveling system", inline = False)
        em.add_field(name = "/slvl setlvl", value = "Allows you to set a user's level", inline = False)
        em.add_field(name = "/slvl setlevelrewards", value = "Allows you to set a Role for each level", inline = False)
        em.add_field(name = "/slvl setlevelupchannel", value = "Allows you to set the Level Up Channel", inline = False)
        em.add_field(name = "/slvl setlevelupmessage", value = "Allows you to set the Level Up Message", inline = False)
        em.add_field(name = "/slvl resetlevelupmessage", value = "Allows you to reset the levelup message", inline = False)
        return em
    

    """
    The function `createPollEmbed` creates a Discord embed with a title, a description indicating the
    remaining time, and options for a poll.
    
    :param title: The title of the poll
    :param minutes: The `minutes` parameter is the number of minutes remaining for the poll. It is used
    to display the remaining time in the poll embed
    :param options: A list of options for the poll. Each option is a string
    :return: The function `createPollEmbed` returns an instance of the `discord.Embed` class.
    """
    async def createPollEmbed(self,title, minutes, options):
        em = discord.Embed(title = title, description = f"You have **{minutes}** minutes remaining!", color=discord.Colour.orange())
        if options[0] != "-":
            for number,option in enumerate(options):
                em.add_field(name = f"{self.numbers[number]}", value = f"**{option}**", inline = False)
        return em


    """
    The function `getLvlAndXp` retrieves a user's XP and level from a database, and if they don't exist,
    inserts them into the database and returns 0 for each.
    
    :param member: The `member` parameter represents a user or member object in a guild or server. It
    could be an instance of a class that represents a user/member in a Discord server, for example
    :param guild: The `guild` parameter represents the guild (server) where the member is located. It is
    used to identify the specific guild in the database query and retrieve the member's xp and level
    information specific to that guild
    :return: the user's xp and level as a tuple.
    """
    async def getLvlAndXp(self, member, guild):
        #*Gets the user's xp and level from the database
        xp_query = "SELECT xp FROM levels WHERE user = ? AND guild = ?"
        xp = self.fetch_from_db(xp_query, (member.id, guild.id))
        level_query = "SELECT level FROM levels WHERE user = ? AND guild = ?"
        level = self.fetch_from_db(level_query, (member.id, guild.id))
        #*If there's no xp or level, insert it into the database and return 0 for each
        if not xp or not level:
            cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)", (0,0,member.id, guild.id))
            database.commit()
            return 0, 0
        #*Return the xp and level
        xp = xp[0][0]
        level = level[0][0]
        return xp, level

    """
    The `createRankImage` function creates a rank image for a user with their profile picture, name,
    level, and XP percentage.
    
    :param member: The `member` parameter is an object representing a member of a Discord server. It
    contains information about the member, such as their username, avatar, and other details
    :param userData: The `userData` parameter is a dictionary that contains information about the user's
    data. It includes the following keys:
    :return: a discord.File object, which represents a file that can be sent in a Discord message. The
    file contains the image generated by the function, with the filename "levelcard.png".
    """
    async def createRankImage(self,member, user_data):
        #*Create a background image
        background = Editor(Canvas((900, 300), color="#141414"))
        #*Load the user's profile picture, resize it and make it a circle
        profile_picture = await load_image_async(str(member.avatar.url))
        profile = Editor(profile_picture).resize((150, 150)).circle_image()

        #*Set the font used for the text
        poppins = Font.poppins(size=40)
        poppins_small = Font.poppins(size=30)

        #*Create the shapes for the card
        card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]

        #*Create the card
        background.polygon(card_right_shape, color="#FFFFFF")
        background.paste(profile, (30,30))
        background.rectangle((30, 220), width=650, height=40, color="#FFFFFF", radius=20)
        background.bar((30, 220), max_width=650, height=40, percentage=user_data["precentage"], color="#282828", radius=20)
        background.text((200, 40), user_data["name"], font=poppins, color="#FFFFFF")
        background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
        background.text((200, 130), f"Level - {user_data['level']} | XP - {int(user_data['xp'])}%", font=poppins_small, color="#FFFFFF")

        #*Return the image as a file
        file = discord.File(fp=background.image_bytes, filename="levelcard.png")

        return file


    """
    The function `createRoleRewardsEmbrd` creates an embed with role rewards for each level.
    
    :param interaction: The `interaction` parameter is an instance of `discord.Interaction`, which represents the
    interaction context of a command or event in a Discord bot. It contains information about the user,
    the channel, the guild, and other relevant data related to the interaction
    :type interaction: discord.Interaction
    :param role_rewards: role_rewards is a list of tuples, where each tuple contains information about a
    role reward. Each tuple has three elements:
    :return: an embed object (`discord.Embed`) that contains information about the role rewards for each
    level.
    """
    async def createRoleRewardsEmbrd(self, interaction : discord.Interaction, role_rewards):
        #*Create the embed
        em = discord.Embed(title="Rewards", description="These are the rewards for each level", color=discord.Colour.orange())
        #*Add the rewards to the embed
        for role in role_rewards:
            role_obj = interaction.guild.get_role(role[1])
            role_name = role_obj.mention if role_obj else "Role not found"
            em.add_field(name=f"Level {role[2]}", value=role_name, inline=False)
        return em
    
    """
    The function `createLevelLeaderBoardEmbed` creates an embed for a leaderboard with user data and
    returns it.
    
    :param data: The `data` parameter is a list of user data. Each element in the list represents a user
    and contains their level, XP, and user ID
    :param interaction: interaction is an object that represents the context of the command being executed. It contains
    information such as the message, the author, the server, and other relevant details
    :return: an embed object (`discord.Embed`) that contains the leaderboard information for the
    server's users.
    """
    async def createLevelLeaderBoardEmbed(self,data,interaction):
        #*Gets the number of users in the server
        users_count = len(data)
        #*Creates the embed
        em = discord.Embed(title="Leaderboard", description=f"These are the top {users_count} users in the server", color=discord.Colour.orange())
        #* The enumerate function is used to get the index and user data in the loop
        for index, user_data in enumerate(data, start=1):
            user = interaction.guild.get_member(user_data[2])
            field_name = f"{index}. {user.display_name}"
            field_value = f"Level: **{user_data[0]}** | XP: **{user_data[1]}**"
            em.add_field(name=field_name, value=field_value, inline=False)
        return em


    """
    The `get_score` function retrieves the user's score from the database and if it doesn't exist,
    inserts it into the database with a default value of 0.
    
    :param interaction: interaction is an object that represents the context of the current command or event. It
    typically contains information such as the guild (server) ID, user ID, and other relevant data for
    the command or event being executed
    :return: the user's score. If the score is found in the database, it will return the score value. If
    the score is not found, it will insert a score of 0 into the database and return 0.
    """
    def get_score(self, interaction):
        #*Gets the user's score from the database
        score_query = "SELECT score FROM rps WHERE guild_id = ? AND user_id = ?"
        score = self.fetch_from_db(score_query, (interaction.guild.id, interaction.user.id))
        #*If there's no score, insert it into the database
        if not score:
            query = "INSERT INTO rps VALUES (?,?,?)"
            self.execute_db_query(query, (interaction.guild.id, interaction.user.id, 0))
            return 0
        else:
            return score[0]

    """
    The function determines the result of a game based on the user's and bot's hand gestures.
    
    :param user_hand: The user's hand gesture in the game (e.g., "✌️" for a peace sign, "✋" for a raised
    hand, "🤜" for a fist bump)
    :param bot_hand: The `bot_hand` parameter represents the hand gesture made by the bot in a game. It
    can be one of the following hand gestures: "✌️" (representing a peace sign), "✋" (representing a
    raised hand), or "🤜" (representing
    :return: a tuple containing the result of the game (either "It's a Draw!", "I won!", or "You won!")
    and the corresponding discord.Colour object (either discord.Colour.orange(), discord.Colour.red(),
    or discord.Colour.green()).
    """
    def determine_game_result(self, user_hand, bot_hand):
        #*Determines the result of the game
        if user_hand == bot_hand:
            return "It's a Draw!", discord.Colour.orange()
        if (user_hand == "✌️" and bot_hand == "🤜") or (user_hand == "✋" and bot_hand == "✌️") or (user_hand == "🤜" and bot_hand == "✋"):
            return "I won!", discord.Colour.red()
        return "You won!", discord.Colour.green()


    """
    The function sends a game result message with the user's and bot's hands, the score, and a specified
    color.
    
    :param interaction: The `interaction` parameter is an object that represents the context of the command being
    executed. It contains information such as the message that triggered the command, the channel it was
    sent in, the author of the message, and more. It is typically passed as the first parameter to
    command functions in discord.py
    :param result: The result of the game (e.g., "You win!", "You lose!", "It's a tie!")
    :param user_hand: The `user_hand` parameter represents the hand that the user chose in the game. It
    could be a string representing the user's choice, such as "rock", "paper", or "scissors"
    :param bot_hand: The parameter `bot_hand` represents the hand that the bot chose in the game. It is
    a string value that should be passed to the `value` parameter of the `embed.add_field()` method
    :param score: The "score" parameter is a list that contains the score of the game. It is expected to
    have only one element, which represents the score of the player
    :param color: The "color" parameter in the "send_game_result" function is used to specify the color
    of the embed message. It is a value that represents the color of the embed message, and it is used
    to visually distinguish different types of messages or to match the theme of the bot. The color
    parameter
    """
    async def send_game_result(self, interaction, result, user_hand, bot_hand, score, color):
        embed = discord.Embed(title=result, description="Here's the result of the game", color=color)
        embed.add_field(name="You chose:", value=user_hand, inline=False)
        embed.add_field(name="I chose:", value=bot_hand, inline=False)
        embed.add_field(name="Score:", value=score[0], inline=False)
        await interaction.response.send_message(embed=embed)


    """
    The function creates and returns an embed object with the given score for a Rock-Paper-Scissors
    game.
    
    :param score: The `score` parameter in the `create_score_embed` function is the score of the user's
    Rock-Paper-Scissors game. It is used to display the score in the embed message
    :return: an instance of the `discord.Embed` class.
    """
    async def create_score_embed(self, score):
        em = discord.Embed(title="Your RPS Stats", description="These are your RPS Stats", color=discord.Colour.orange())
        em.add_field(name="Score:", value=score[0], inline=False)
        return em
    

    """
    The function `create_leaderboard_embed` creates a Discord embed object for displaying a
    Rock-Paper-Scissors leaderboard.
    
    :param scores: The `scores` parameter is a list of tuples. Each tuple contains two elements: the
    first element is the user ID, and the second element is the score
    :return: an instance of the `discord.Embed` class, which represents an embedded message in Discord.
    """
    async def create_leaderboard_embed(self, scores):
        em = discord.Embed(title="RPS Leaderboard", description="These is the RPS Leaderboard", color=discord.Colour.orange())
        for score in scores:
            user = await self.bot.fetch_user(score[0])
            em.add_field(name=f"{user.display_name}", value=f"Score: {score[1]}", inline=False)
        return em
    

    """
    The function `find_banned_user` searches for a user in a list of banned members and returns the user
    if found, otherwise it returns None.
    
    :param banned_members: A list of objects representing banned members. Each object has a property
    called "user" which contains information about the banned user, including their name
    :param user_to_unban: The user name of the user that needs to be unbanned
    :return: the user object of the banned member if the user to unban is found in the list of banned
    members. If the user to unban is not found, it returns None.
    """
    def find_banned_user(self, banned_members, user_to_unban):
        for banned_member in banned_members:
            if user_to_unban == banned_member.user.name:
                return banned_member.user
        return None
    
    
    """
    The function `purge_messages_by_date` deletes all messages in a channel after a specified date and
    sends a confirmation message.
    
    :param interaction: The `interaction` parameter is an object that represents the context of the command being
    executed. It contains information about the message, the channel, the server, and the user who
    triggered the command
    :param day: The day parameter represents the day of the month for which you want to delete messages.
    It should be an integer value between 1 and 31
    :param month: The `month` parameter in the `purge_messages_by_date` function represents the month of
    the date after which you want to delete messages. It should be an integer value between 1 and 12,
    representing the months from January to December
    :param year: The year parameter represents the year of the date after which you want to delete
    messages
    """
    async def purge_messages_by_date(self, interaction, day, month, year):
        await interaction.channel.purge(after=datetime(year, month, day))
        await interaction.channel.send(f"Deleted all messages after {day}/{month}/{year}")

    """
    The function `purge_messages_by_limit` deletes a specified number of messages in a channel and
    sends a message confirming the number of messages deleted.
    
    :param interaction: interaction is the interaction object, which contains information about the current state of the
    bot and the message that triggered the command. It includes attributes such as the channel,
    user, guild, and message content
    :param limit: The `limit` parameter in the `purge_messages_by_limit` function is the number of
    messages to be deleted from the channel. It specifies the maximum number of messages to be
    deleted, including the command message itself
    """
    async def purge_messages_by_limit(self, interaction, limit):
        await interaction.channel.purge(limit=int(limit) + 1)
        await interaction.channel.send(f"Deleted {limit} messages")
    

    """
    The function executes a database query with the given query and parameters, and commits the changes
    to the database.
    
    :param query: The query parameter is a string that represents the SQL query you want to execute on
    the database. It can be any valid SQL statement, such as SELECT, INSERT, UPDATE, DELETE, etc
    :param params: The "params" parameter is a tuple or list that contains the values to be substituted
    into the query. These values are used to replace the placeholders in the query string. The
    placeholders are typically represented by question marks (?) or percent signs (%s) in the query
    string. The values in the "params
    """
    def execute_db_query(self, query, params):
        cursor.execute(query, params)
        database.commit()
    
    """
    The function fetches data from a database using a given query and parameters.
    
    :param query: The query parameter is a string that represents the SQL query you want to execute on
    the database. It only accepts SELECT statements.
    :param params: The "params" parameter is a tuple that contains the values to be substituted into the
    query string. These values are used to replace the placeholders in the query string, if any. The
    placeholders are typically represented by question marks (?) or percent signs (%s) in the query
    string
    :return: The fetch_from_db function is returning the result of the cursor.fetchall() method, which
    is a list of all the rows returned by the query execution.
    """
    def fetch_from_db(self, query, params):
        cursor.execute(query, params)
        return cursor.fetchall()
    
async def setup(bot) -> None:
    await bot.add_cog(CommandHandler(bot))