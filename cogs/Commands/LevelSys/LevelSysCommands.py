import discord
from discord import app_commands
from discord.ext import commands
from cogs.DatabaseHandler import DatabaseHandler
from cogs.Commands.LevelSys.LevelUtils import LevelUtils
from cogs.constants import (
    LEVELSYS_QUERY,
    LVLSYS_DISABLED,
)

class LevelSysCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()
        self.level_utils = LevelUtils(bot)

    #* Sends an image with the user's current rank
    @app_commands.command(name= "rank", description="Shows your level!")
    async def rank(self, interaction : discord.Interaction, member: discord.Member = None):
        #*If no member is specified, use the user
        if member is None:
            member = interaction.user

        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (interaction.guild.id,))


        if not levelsys[0]:
            await interaction.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return
        
        xp, level = await self.level_utils.getLvlAndXp(member, interaction.guild)

        user_data = {
            "name" : member.display_name,
            "xp" : xp,
            "level" : level,
            "nextLevelXp" : 100,
            "precentage" : xp
        }

        file = await self.level_utils.createRankImage(member, user_data)
        await interaction.response.send_message(file=file)

    #*Sends a message with the rewards for each level
    @app_commands.command(name="rewards", description="Lets you see the rewards for each level")
    async def rewards(self, interaction : discord.Interaction):
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (interaction.guild.id,))

        if not levelsys[0]:
            await interaction.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return
        
        #* Fetch role rewards
        role_rewards_query = "SELECT * FROM levelsettings WHERE guild_id = ?"
        role_rewards = self.database.fetch_all_from_db(role_rewards_query, (interaction.guild.id,))
        role_rewards = role_rewards[1:]

        #* If there are no rewards, send a message
        if not role_rewards:
            await interaction.response.send_message("There are no rewards set for this server!", ephemeral=True, delete_after=5)
            return
        #* Create embed for role rewards
        em = await self.level_utils.createRoleRewardsEmbed(interaction, role_rewards)

        await interaction.response.send_message(embed=em)

    #* Sends a message with the guild's level leaderboard
    @app_commands.command(name="leaderboard", description="Displays the server's leaderboard")
    async def leaderboard(self, interaction : discord.Interaction):
        #* Check if leveling system is enabled
        levelsys_query = LEVELSYS_QUERY
        levelsys = self.database.fetch_one_from_db(levelsys_query, (interaction.guild.id,))

        if not levelsys[0]:
            await interaction.response.send_message(LVLSYS_DISABLED, ephemeral=True, delete_after=5)
            return
        
        #* Fetch leaderboard data
        data_query = "SELECT level, xp, user FROM levels WHERE guild = ? ORDER BY level DESC, xp DESC LIMIT 10"
        data = self.database.fetch_all_from_db(data_query, (interaction.guild.id,))

        #*If there's data, create the embed and send it
        if data:
            em = await self.level_utils.createLevelLeaderBoardEmbed(data, interaction)
            await interaction.response.send_message(embed=em)
            return

        return await interaction.response.send_message("There are no users in the leaderboard!", ephemeral=True, delete_after=5)


async def setup(bot):
    await bot.add_cog(LevelSysCommands(bot))