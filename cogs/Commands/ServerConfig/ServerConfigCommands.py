import discord
from discord import app_commands
from discord.ext import commands
from cogs.DatabaseHandler import DatabaseHandler
from cogs.constants import NO_PERMS_MESSAGE

class ServerConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()

    """This group of commands allows the user to edit the server settings"""
    serverGroup = app_commands.Group(name = "editserver", description="Edit Server Settings")

    @serverGroup.command(name="servername", description="Edits the Server Name")
    @app_commands.describe(input = "The new Server Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def servername(self,interaction : discord.Interaction,input : str):
        await interaction.guild.edit(name = input)
        await interaction.response.send_message(f"Server Name Changed to {input}", ephemeral=True, delete_after=5)

    @serverGroup.command(name="region", description="Edits the Server Region")
    @app_commands.describe(input = "The new Server Region")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def region(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.edit(region = input)
        await interaction.response.send_message(f"Server Region Changed to {input}", ephemeral=True, delete_after=5)

    @serverGroup.command(name="createtextchannel", description="Creates a Text Channel")
    @app_commands.describe(input = "The new Text Channel Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createtextchannel(self,interaction : discord.Interaction,input : str):
        await interaction.guild.create_text_channel(name = input)
        await interaction.response.send_message(f"Text Channel Created with the name {input}", ephemeral=True, delete_after=5)

    @serverGroup.command(name="createvoicechannel", description="Creates a Voice Channel")
    @app_commands.describe(input = "The new Voice Channel Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createvoicechannel(self,interaction : discord.Interaction,input : str):
        await interaction.guild.create_voice_channel(name = input)
        await interaction.response.send_message(f"Voice Channel Created with the name {input}", ephemeral=True, delete_after=5)

    @serverGroup.command(name="createrole", description="Creates a Role")
    @app_commands.describe(input = "The new Role Name")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def createrole(self,interaction : discord.Interaction,*,input : str):
        await interaction.guild.create_role(name = input)
        await interaction.response.send_message(f"Role Created with the name {input}")

    #* Error Handling
    @servername.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @region.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)
        if isinstance(error, app_commands.errors.CommandInvokeError):
            await interaction.response.send_message("Please choose a valid region!", ephemeral=True, delete_after=5)

    @createtextchannel.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

    @createvoicechannel.error
    async def errorhandler(self, interaction : discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True, delete_after=5)

async def setup(bot):
    await bot.add_cog(ServerConfigCommands(bot))