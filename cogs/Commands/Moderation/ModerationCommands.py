import discord
from discord import app_commands
from datetime import datetime
from discord.ext import commands
from cogs.Commands.Moderation.ModerationUtils import ModerationUtils
from cogs.constants import NO_PERMS_MESSAGE

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderation_utils = ModerationUtils(bot)

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
    async def unban(self, interaction: discord.Interaction, user_to_unban: str):
        try:
            banlist = interaction.guild.bans()
            banlist = [ban async for ban in banlist]
            user = await self.moderation_utils.find_banned_user(banlist, user_to_unban)
        
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"Unbanned {user}", ephemeral=True, delete_after=5)
            
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Unable to unban {user_to_unban}", ephemeral=True, delete_after=5)

                
    @moderationGroup.command(name="purge", description="Clears X amount of messages from a channel")
    @app_commands.describe(message_limit_or_date_indicator = "The amount of messages to delete", day = "The day to delete from", month = "The month to delete from", year = "The year to delete from")
    @app_commands.checks.has_permissions(manage_messages = True)
    async def purge(self, interaction: discord.Interaction, message_limit_or_date_indicator: int, day: int = None, month: int = None, year: int = datetime.now().year):
        if str(message_limit_or_date_indicator) == "/":
            if day is None or month is None:
                return await interaction.response.send_message("Please specify a date!", ephemeral=True, delete_after=5)
            else:
                await interaction.response.send_message(f"Purging messages from {day}/{month}/{year}", ephemeral=True, delete_after=5)
                await self.moderation_utils.purge_messages_by_date(interaction, day, month, year)
        else:
            await interaction.response.send_message(f"Purging {message_limit_or_date_indicator} messages", ephemeral=True, delete_after=5)
            await self.moderation_utils.purge_messages_by_limit(interaction, message_limit_or_date_indicator)

    @moderationGroup.command(name="mute", description="Mutes a user")
    @app_commands.describe(user = "The user to mute")
    @app_commands.checks.has_permissions(mute_members = True)
    async def mute(self, interaction : discord.Interaction, user : discord.Member):
        try:
            await user.edit(mute = True)
            await interaction.response.send_message(f"Muted {user}", ephemeral=True, delete_after=5)
        except Exception as e:
            await interaction.response.send_message(f"Unable to mute {user}", ephemeral=True, delete_after=5)

    @moderationGroup.command(name="unmute", description="Unmutes a user")
    @app_commands.describe(user = "The user to unmute")
    @app_commands.checks.has_permissions(mute_members = True)
    async def unmute(self,interaction : discord.Interaction, user : discord.Member ):
        try:
            await user.edit(mute = False)
            await interaction.response.send_message(f"Unmuted {user}", ephemeral=True, delete_after=5)
        except Exception as e:
            await interaction.response.send_message(f"Unable to unmute {user}", ephemeral=True, delete_after=5)

    @moderationGroup.command(name="deafen", description="Deafens a user")
    @app_commands.describe(user = "The user to deafen")
    @app_commands.checks.has_permissions(deafen_members = True)
    async def deafen(self,interaction : discord.Interaction, user : discord.Member):
        try:
            await user.edit(deafen = True)
            await interaction.response.send_message(f"Deafened {user}", ephemeral=True, delete_after=5)
        except Exception as e:
            await interaction.response.send_message(f"Unable to deafen {user}", ephemeral=True, delete_after=5)

    @moderationGroup.command(name="undeafen", description="Undeafens a user")
    @app_commands.describe(user = "The user to undeafen")
    @app_commands.checks.has_permissions(deafen_members = True)
    async def undeafen(self,interaction : discord.Interaction, user : discord.Member):
        try:
            await user.edit(deafen = False)
            await interaction.response.send_message(f"Undeafened {user}", ephemeral=True, delete_after=5)
        except Exception as e:
            await interaction.response.send_message(f"Unable to undeafen {user}", ephemeral=True, delete_after=5)

    @moderationGroup.command(name="voicekick", description="Kicks a user from a Voice Channel")
    @app_commands.describe(user = "The user to kick from the Voice Channel")
    @app_commands.checks.has_permissions(kick_members = True)
    async def voicekick(self,interaction : discord.Interaction, user : discord.Member):
        try:
            await user.edit(voice_channel = None)
            await interaction.response.send_message(f"Kicked {user} from Voice Channel", ephemeral=True, delete_after=5)
        except Exception as e:
            await interaction.response.send_message(f"Unable to kick {user} from Voice Channel", ephemeral=True, delete_after=5)

    
    #* Error Handling
    @kick.error
    async def errorhandler(self,interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @ban.error
    async def errorhandler(self,interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)
    @purge.error
    async def errorhandler(self,interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @deafen.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @undeafen.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @mute.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @unmute.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @voicekick.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)
    
    @unban.error
    async def errorhandler(self,interaction : discord.Interaction, error):    
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)


async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))