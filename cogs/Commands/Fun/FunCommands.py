
import aiohttp
import discord
from discord import app_commands
from discord.app_commands import Choice
import random
from discord.ext import commands
from cogs.DatabaseHandler import DatabaseHandler
from cogs.Commands.Fun.FunCommandsUtils import FunCommandsUtils
from cogs.constants import (
    API_URL,
)

class FunCommands(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()
        self.utils = FunCommandsUtils(bot, self.database)

    #* Fun Commands
    #* Ping Command, replies with Pong! and the latency of the bot
    @app_commands.command(name="ping", description="Pings the bot")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, interaction : discord.Interaction):
        await interaction.response.send_message(f"Pong! 🏓  {self.bot.latency * 1000:.0f}ms")

    @app_commands.command(name="joke", description="Sends a random joke")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def joke(self, interaction : discord.Interaction):
        async with aiohttp.ClientSession() as session:
            headers = {"Accept": "application/json", "User-Agent": "VeloxDiscordBot (https://github.com/FernandoJVideira/VeloxDiscordBot)"}
            async with session.get(API_URL, headers=headers) as response:
                data = await response.json()
                await interaction.response.send_message(data["joke"])

    #* Sends a message with a coinflip
    @app_commands.command(name="coinflip", description="Flips a coin")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def coinflip(self,interaction : discord.Interaction):
        #* Generates a random number between 1 and 2
        num = random.randint(1, 2)
        #* If the number is 1, send Heads!, if it's 2, send Tails!
        if num == 1:
            await interaction.response.send_message("Heads!")
        if num == 2:
            await interaction.response.send_message("Tails!")

    @app_commands.command(name="dice", description="Rolls a dice")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def dice(self,interaction : discord.Interaction, dice: str):
        pattern_index = await self.utils.matches_template(dice)
        if pattern_index is not None:
            match pattern_index:
                case 1 | 0:
                    text = await self.utils.sum_rolled_dice(dice)
                    await interaction.response.send_message(text)                  
                case 2:
                    num_dice, dice_type, modifier, modifier_line = await self.parse_separate_dice(dice) 
                    messages = await self.utils.roll_multiple_dice(num_dice, dice_type, modifier, modifier_line)
                    await interaction.response.send_message('\n'.join(messages))

    
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
            return await interaction.response.send_message("Invalid hand! Please choose between ✌️, ✋ or 🤜", ephemeral=True, delete_after=5)
        #* Gets the user's score 
        score = await self.utils.get_score(interaction)
        #* If the user wins the returned color is green, otherwise it's red
        #* The result is the game result
        result, color = await self.utils.determine_game_result(hand, bot_hand)
        #* Updates the user's score
        if result == "You won!":
            new_score = score[0] + 1
            query = "UPDATE rps SET score = ? WHERE guild_id = ? AND user_id = ?"
            self.database.execute_db_query(query, (new_score, interaction.guild.id, interaction.user.id))
        #* Sends the game result
        await self.utils.send_game_result(interaction, result, hand, bot_hand, new_score, color)

    #* Shows the user's RPS Stats
    @app_commands.command(name="rpsstats", description="Shows your RPS Stats")
    async def rpsstats(self, interaction: discord.Interaction):
        #* Fetch user's score
        user_score_query = "SELECT score FROM rps WHERE guild_id = ? AND user_id = ?"
        user_score = self.database.fetch_one_from_db(user_score_query, (interaction.guild.id, interaction.user.id))

        #* If the user has played RPS, create the embed and send it
        if user_score is not None:
            user_score = user_score[0]
            embed = await self.utils.create_score_embed(user_score)
            await interaction.response.send_message(embed=embed)
        else:
            #* If the user hasn't played RPS, send a message
            await interaction.response.send_message("You haven't played RPS yet!", ephemeral=True, delete_after=5)
    
    @app_commands.command(name="rpsleaderboard", description="Shows the RPS Leaderboard")
    async def rpsleaderboard(self, interaction: discord.Interaction):
        #* Fetch leaderboard scores
        leaderboard_query = "SELECT user_id, score FROM rps WHERE guild_id = ? ORDER BY score DESC"
        leaderboard_scores = self.database.fetch_all_from_db(leaderboard_query, (interaction.guild.id,))
        
        #* If there's data, create the embed and send it
        if leaderboard_scores is not None:
            embed = await self.utils.create_leaderboard_embed(leaderboard_scores)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Shows the bot's commands")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
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
                fun_embed = await self.utils.createFunCmdEmbed()
                music_embed = await self.utils.createMusicCmdEmbed()
                mod_embed = await self.utils.createAdminCmdEmbed()
                config_embed = await self.utils.createConfigCmdEmbed()
                leveling_embed = await self.utils.createLevelingEmbed()
                embeds.extend([fun_embed, music_embed, mod_embed, config_embed, leveling_embed])
            case "fun":
                fun_embed = await self.utils.createFunCmdEmbed()
                embeds.append(fun_embed)
            case "music":
                music_embed = await self.utils.createMusicCmdEmbed()
                embeds.append(music_embed)
            case "config":
                config_embed = await self.utils.createConfigCmdEmbed()
                embeds.append(config_embed)
            case "moderation":
                mod_embed = await self.utils.createAdminCmdEmbed()
                embeds.append(mod_embed)
            case "levelingsys":
                leveling_embed = await self.utils.createLevelingEmbed()
                embeds.append(leveling_embed)

        #* Creates the dm channel and sends the embeds
        await interaction.response.send_message("Check your DMs!", ephemeral=True, delete_after=5)
        await interaction.user.create_dm()
        for em in embeds:
            await interaction.user.dm_channel.send(embed = em)
    
async def setup(bot) -> None:
    await bot.add_cog(FunCommands(bot))