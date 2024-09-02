import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from cogs.DatabaseHandler import DatabaseHandler
from cogs.Commands.Config.BotConfigUtils import BotConfigUtils


class BotConfig(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()
        self.utils = BotConfigUtils(self.database)


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
        self.database.execute_db_query(query, (channel_id, guild_id))

        await interaction.response.send_message(f"Welcome Channel set to {welcome_channel.mention}", ephemeral=True, delete_after=5)

    @config.command(name="removewelcomechannel", description="Removes the Channel set for Welcome Messages")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeWelcomeChannel(self,interaction : discord.Interaction):
        #* Deletes the welcome channel from the database
        query = "DELETE FROM welcome WHERE guild_id = ?"
        self.database.execute_db_query(query, (interaction.guild.id,))
        #* Sends a message
        await interaction.response.send_message("Removed the Welcome Channel!", ephemeral=True, delete_after=5)

    @config.command(name="updatewelcomemessage", description="Updates the Default Welcome Embed Message")
    @app_commands.describe(message = "The new Welcome Message")
    async def updateWelcomeMessage(self,interaction : discord.Interaction, *, message : str):
        query = "UPDATE welcome SET welcome_message = ? WHERE guild_id = ?"
        self.database.execute_db_query(query, (message, interaction.guild.id))
        await interaction.response.send_message("Welcome Message Updated!", ephemeral=True, delete_after=5)

    @config.command(name="updatewelcomedm", description="Updates the Default Welcome DM Message")
    @app_commands.describe(message = "The new Welcome DM Message")
    async def updateWelcomeDmMessage(self,interaction : discord.Interaction, *, message : str):
        query = "UPDATE welcome SET welcome_dm = ? WHERE guild_id = ?"
        self.database.execute_db_query(query, (message, interaction.guild.id))
        await interaction.response.send_message("Welcome Message DM Updated!", ephemeral=True, delete_after=5)

    @config.command(name="updatewelcomegif", description="Updates the Default Welcome Embed Gif")
    @app_commands.describe(url = "The new Welcome Gif URL")
    async def updateWelcomeGif(self,interaction : discord.Interaction, *, url : str):
        query = "UPDATE welcome SET welcome_gif_url = ? WHERE guild_id = ?"
        self.database.execute_db_query(query, (url, interaction.guild.id))
        await interaction.response.send_message("Welcome Embed Gif Updated!", ephemeral=True, delete_after=5)


    @config.command(name="setlevelupchannel", description="Sets the Level Up Channel")
    @app_commands.describe(levelup_channel = "The channel to set as the Level Up Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setLevelUpChannel(self, command_context: discord.Interaction, levelup_channel: discord.TextChannel):
        #* Gets the guild id and the channel id
        guild_id = command_context.guild.id
        channel_id = levelup_channel.id
        #* Fetches the existing levelup channel, if there is one
        channel_query = "SELECT levelup_channel_id FROM levelup WHERE guild_id = ?"
        existing_levelup_channel = self.database.fetch_one_from_db(channel_query, (guild_id,))
        #* If there's no levelup channel, insert it into the database, otherwise update it
        if not existing_levelup_channel:
            query = "INSERT INTO levelup VALUES (?,?)"
            self.database.execute_db_query(query, (guild_id, channel_id))
        else:
            query = "UPDATE levelup SET levelup_channel_id = ? WHERE guild_id = ?"
            self.database.execute_db_query(query, (guild_id, channel_id))
        #* Sends a message
        await command_context.response.send_message(f"Level Up Channel set to {levelup_channel.mention}", ephemeral=True, delete_after=5)

    @config.command(name="removelevelupchannel", description="Removes the Channel set for Level Up Notifications")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeStreamChannel(self,interaction : discord.Interaction):
        #* Deletes the levelup channel from the database
        query = "DELETE FROM levelup WHERE guild_id = ?"
        self.database.execute_db_query(query, (interaction.guild.id,))
        #* Sends a message
        await interaction.response.send_message("Removed the Level Up Channel!", ephemeral=True, delete_after=5)

    @config.command(name="settwitchnotificationchannel", description="Sets the Channel for Twitch Notifications")
    @app_commands.describe(twitch_notification_channel = "The channel to set as the Notification Channel")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setTwitchNotificationChannel(self, command_context: discord.Interaction, twitch_notification_channel: discord.TextChannel):
        #* Gets the guild id and the channel id
        guild_id = command_context.guild.id
        channel_id = twitch_notification_channel.id
        #* Fetches the existing twitch channel, if there is one
        config_query = "SELECT twitch_channel_id FROM twitch_config WHERE guild_id = ?"
        existing_twitch_config = self.database.fetch_one_from_db(config_query, (guild_id,))
        #* If there's no twitch channel, insert it into the database, otherwise update it
        if not existing_twitch_config:
            query = "INSERT INTO twitch_config VALUES (?,?)"
            self.database.execute_db_query(query, (guild_id, channel_id))
        else:
            query = "UPDATE twitch_config SET twitch_channel_id = ? WHERE guild_id = ?"
            self.database.execute_db_query(query, (guild_id, channel_id))
        #* Sends a message
        await command_context.response.send_message(f"Notification Channel set to {twitch_notification_channel.mention}", ephemeral=True, delete_after=5)
    
    @config.command(name="removestreamchannel", description="Removes the Channel set for Twitch Notifications")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeStreamChannel(self,interaction : discord.Interaction):
        #* Deletes the twitch channel from the database
        query = "DELETE FROM twitch_config WHERE guild_id = ?"
        self.database.execute_db_query(query, (interaction.guild.id,))
        #* Sends a message
        await interaction.response.send_message("Removed the Notification Channel!", ephemeral=True, delete_after=5)

    @config.command(name="addstreamer", description="Adds a Streamer for Twitch Notifications")
    @app_commands.describe(streamer = "The streamer to add")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def addStreamer(self,interaction : discord.Interaction, streamer : str):
        #* Fetches the existing twitch channel, if there is one
        query = "SELECT twitch_channel_id FROM twitch_config WHERE guild_id = ?"
        not_channel = self.database.fetch_one_from_db(query, (interaction.guild.id,))
        #* If there's no twitch channel, send a message, otherwise add the streamer to the database
        if not not_channel:
            await interaction.response.send_message("Please set a Notification Channel first!", ephemeral=True, delete_after=5)
        else:
            streamer = self.utils.checkStreamer(streamer)
            if len(streamer) > 0:
                await interaction.response.send_message("This streamer is already in the Streamers List!", ephemeral=True, delete_after=5)
                return
            query = "INSERT INTO twitch VALUES (?,?,?)"
            self.database.execute_db_query(query, (streamer,"not live", interaction.guild.id))
            await interaction.response.send_message(f"Added {streamer} to the Streamers List!", ephemeral=True, delete_after=5)

    @config.command(name="removestreamer", description="Removes a Streamer from Twitch Notifications")
    @app_commands.describe(streamer = "The streamer to remove")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removeStreamer(self,interaction : discord.Interaction, streamer : str):
        if await self.utils.checkStreamer(streamer) is None:
            await interaction.response.send_message("This streamer is not in the Streamers List!", ephemeral=True, delete_after=5)
            return
        #* Deletes the streamer from the database
        query = "DELETE FROM twitch WHERE twitch_user = ? AND guild_id = ?"
        self.database.execute_db_query(query, (streamer, interaction.guild.id))
        #* Sends a message
        await interaction.response.send_message(f"Removed {streamer} from the Streamers List!", ephemeral=True, delete_after=5)      

    @config.command(name="setdefaultrole", description="Sets the Default Role when a user joins the server")
    @app_commands.describe(default_role = "The role to set as the Default Role")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setDefaultRole(self, command_context: discord.Interaction, default_role: discord.Role):
        #* Gets the guild id and the role id
        guild_id = command_context.guild.id
        role_id = default_role.id
        #* Fetches the existing default role, if there is one
        query = "SELECT * FROM defaultrole WHERE guild_id = ?"
        existing_default_role = self.database.fetch_one_from_db(query, (guild_id,))
        #* If there's no default role, insert it into the database, otherwise update it
        if not existing_default_role:
            query = "INSERT INTO defaultrole VALUES (?,?)"
            self.database.execute_db_query(query, (guild_id, role_id))
        else:
            query = "UPDATE defaultrole SET role_id = ? WHERE guild_id = ?"
            self.database.execute_db_query(query, (role_id, guild_id))
        #* Sends a message
        await command_context.response.send_message(f"Default Role set to {default_role.mention}", ephemeral=True, delete_after=5)  

async def setup(bot):
    await bot.add_cog(BotConfig(bot))