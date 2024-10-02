import discord
from discord import app_commands
from discord.ext import commands
from cogs.DatabaseHandler import DatabaseHandler
from cogs.constants import (
    LEVELSYS_QUERY,
    LVLSYS_DISABLED,
    LVLSYS_INSERT_QUERY
)

class LevelSysConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()


    """This group of commands allows the user to configure the Server Leveling System"""
    slvl = app_commands.Group(name="slvl", description="Configure the Server Leveling System")

    @slvl.command(name="enable", description="Enables the Server Leveling System")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def enable(self, command_context: discord.Interaction):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Fetches the existing levelsys, if there is one
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))

        #* If there's no levelsys, insert it into the database, otherwise update it
        if not levelsys:
            query = LVLSYS_INSERT_QUERY
            self.database.execute_db_query(query, (True, 0, 0, None, guild_id))
        else:
            #*If the levelsys is already enabled, send a message 
            if levelsys[0]:
                await command_context.response.send_message("The Leveling System is already enabled!", ephemeral=True, delete_after=5)
                return
            query = "UPDATE levelsettings SET levelsys = ? WHERE guild_id = ?"
            self.database.execute_db_query(query, (True, guild_id))
        #* Sends a message
        await command_context.response.send_message("Leveling System Enabled!", ephemeral=True, delete_after=5)

    @slvl.command(name="disable", description="Disables the Server Leveling System")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def disable(self,interaction : discord.Interaction):
        #* Gets the guild id
        guild_id = interaction.guild.id
        #* Fetches the existing levelsys, if there is one
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))

        #* If there's no levelsys, insert it into the database, otherwise update it
        if not levelsys:
            query = LVLSYS_INSERT_QUERY
            self.database.execute_db_query(query, (False, 0, 0, None, guild_id))
        else:
            #* If the levelsys is already enabled, send a message
            if not levelsys[0]:
                await interaction.response.send_message("The Leveling System is already disabled!", ephemeral=True, delete_after=5)
                return
            query = "UPDATE levelsettings SET levelsys = ? WHERE guild_id = ?"
            self.database.execute_db_query(query, (False, guild_id))
        #* Sends a message
        await interaction.response.send_message("Leveling System Disabled!", ephemeral=True, delete_after=5)

    @slvl.command(name="setlevelrewards", description="Sets the Level Rewards")
    @app_commands.describe(reward_level = "The level to set the reward for", reward_role = "The role to give as a reward")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setrole(self, command_context: discord.Interaction, reward_level: int, *, reward_role: discord.Role):
        #* Gets the guild id and the role id
        guild_id = command_context.guild.id
        role_id = reward_role.id

        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))

        if not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return
        
        #* Fetches the existing reward role, if there is one
        role_tf_query = "SELECT role FROM levelsettings WHERE role = ? AND guild_id = ?"
        role_tf = self.database.fetch_one_from_db(role_tf_query, (role_id, guild_id))
        level_tf_query = "SELECT role FROM levelsettings WHERE levelreq = ? AND guild_id = ?"
        level_tf = self.database.fetch_one_from_db(level_tf_query, (reward_level, guild_id))

        #* If there's no reward role, insert it into the database, otherwise update it
        if role_tf and level_tf:
            await command_context.response.send_message("This role is already set as a reward for this level!", ephemeral=True, delete_after=5)
            return
        
        #* If there's no reward role, insert it into the database, otherwise update it
        query = "SELECT message FROM levelsettings WHERE guild_id = ?"
        existing_message = self.database.fetch_one_from_db(query, (guild_id,))
        existing_message = existing_message[0] if existing_message else None

        query = "INSERT INTO levelsettings VALUES (?,?,?,?,?)"
        self.database.execute_db_query(query, (True, role_id, reward_level, existing_message, guild_id))
        await command_context.response.send_message(f"Set {reward_role.mention} as a reward for level {reward_level}!", ephemeral=True, delete_after=5)
    
    @slvl.command(name="removereward", description="Removes a Level Reward")
    @app_commands.describe(reward_level = "The level to remove the reward from")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def removereward(self, command_context: discord.Interaction, reward_level: int):
        #* Gets the guild id
        guild_id = command_context.guild.id

        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))

        if not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return

        #* Fetches the existing reward role, if there is one
        query = "DELETE FROM levelsettings WHERE levelreq = ? AND guild_id = ?"
        self.database.execute_db_query(query, (reward_level, guild_id))
        await command_context.response.send_message(f"Removed the reward for level {reward_level}!", ephemeral=True, delete_after=5)

    @slvl.command(name="setlvlupmessage", description="Sets the Level Up Message")
    @app_commands.describe(level_up_message = " {user} is the user that leveled up and {level} is the level the user leveled up to")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setlvlupmessage(self, command_context: discord.Interaction, *, level_up_message: str):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))
        #* If the leveling system is disabled, send a message
        if not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return

        #* Fetches the existing level up message, if there is one
        level_up_message_query = "SELECT message FROM levelsettings WHERE guild_id = ?"
        lvlupmessage = self.database.fetch_one_from_db(level_up_message_query, (guild_id,))

        #* If there's no level up message, insert it into the database, otherwise update it
        if lvlupmessage:
            query = "UPDATE levelsettings SET message = ? WHERE guild_id = ?"
            self.database.execute_db_query(query, (level_up_message, guild_id))
        else:
            query = LVLSYS_INSERT_QUERY
            self.database.execute_db_query(query, (True, 0, 0, level_up_message, guild_id))

        #* Sends a message
        await command_context.response.send_message("Level Up Message set!", ephemeral=True, delete_after=5)
    
    @slvl.command(name="resetlvlupmessage", description="Resets the Level Up Message")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def resetlvlupmessage(self, command_context: discord.Interaction):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))
        #* If the leveling system is disabled, send a message
        if not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return
        #* Resets the level up message
        query = "UPDATE levelsettings SET message = ? WHERE guild_id = ?"
        self.database.execute_db_query(query, (None, guild_id))
        await command_context.response.send_message("Level Up Message reset!", ephemeral=True, delete_after=5)

    @slvl.command(name="setlvl", description="Sets the User's Level")
    @app_commands.describe(user = "The user to set the level for", level = "The level to set")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def setlvl(self, command_context: discord.Interaction, user: discord.Member, level: int):
        #* Gets the guild id
        guild_id = command_context.guild.id
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (guild_id,))
        #* If the leveling system is disabled, send a message
        if not levelsys[0]:
            await command_context.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return
        #* Fetches the existing level, if there is one
        level_query = "SELECT level FROM levels WHERE user = ? AND guild = ?"
        existing_level = self.database.fetch_one_from_db(level_query, (user.id, guild_id))
        #* If there's no level, insert it into the database, otherwise update it
        if existing_level:
            #Set the level to the new level and xp 0
            query = "UPDATE levels SET level = ?, xp = ? WHERE user = ? AND guild = ?"
            self.database.execute_db_query(query, (level, 0, user.id, guild_id))
        else:
            query = "INSERT INTO levels VALUES (?,?,?,?)"
            self.database.execute_db_query(query, (level, 0, user.id, guild_id))
        #* Sends a message
        await command_context.response.send_message(f"Set {user.mention}'s level to {level}!", ephemeral=True, delete_after=5)

async def setup(bot) -> None:
    await bot.add_cog(LevelSysConfig(bot))