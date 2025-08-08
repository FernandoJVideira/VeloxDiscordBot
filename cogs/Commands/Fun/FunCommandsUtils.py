import re
import discord
import random
from cogs.DatabaseHandler import DatabaseHandler
from cogs.constants import (
    EMBED_IMAGE,
)

class FunCommandsUtils:
    def __init__(self, bot, database: DatabaseHandler):
        self.bot = bot
        self.database = database

    #*Utility Functions

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
                total += await self.calculate_dice_sum(rolls, modifier, sign)
                all_rolls.append(roll_str)
            else:
                total += int(part)
        return f'` {max(0,total)} ` ⟵ {all_rolls} {original_dice}'

    async def calculate_dice_sum(self, rolls, modifier, sign):
        if modifier:
            if sign == '-':
                return sum(rolls) - modifier
            else:
                return sum(rolls) + modifier
        else:
            return sum(rolls)


    async def parse_dice_str(self, dice_str: str) -> tuple:
        num_dice, dice_type = 1, 20  # Default values
        modifier = 0  # Default modifier

        parts = dice_str.replace('-', '+-').split('+')  # Split the dice string into parts

        for part in parts:
            part = part.replace(' ', '')  # Remove any spaces in the part
            if 'd' in part:
                #* If the part is another dice roll, parse it separately
                part_dice_str, part_type_str = part.split('d')  # Split the part into the number of dice and the type of dice
                if part_dice_str == '':  #* If the number of dice is not specified, assume it is 1
                    part_dice_str = '1'
                if part_dice_str and part_type_str:  # Check that both strings are not empty
                    part_dice, part_type = map(int, (part_dice_str, part_type_str))  # Convert the strings to integers
                    num_dice = part_dice # Set the number of dice to the parsed value if it is not empty
                    dice_type = part_type  # Assume all dice have the same type
            else:
                modifier = int(part) if part != '' else 0 # Convert the part to an integer and add it to the modifier

        return num_dice, dice_type, modifier
    

    async def roll_single_dice(self, dice_str: str):
        num_dice, dice_type, modifier = await self.parse_dice_str(dice_str)
        rolls = [await self.roll_dice(dice_type) for _ in range(num_dice)]
        roll_strs = [f'**{roll}**' if roll in [1, dice_type] else str(roll) for roll in rolls]
        return rolls, ", ".join(roll_strs), modifier
    

    async def roll_multiple_dice(self, num_dice, dice_type, modifier, modifier_line) -> list:
        messages = []
        for _ in range(num_dice):
            roll = await self.roll_dice(dice_type)
            roll_str = f'**{roll}**' if roll in [1, dice_type] else str(roll)
            total = max(0, roll + modifier)
            messages.append(f'` {total} ` ⟵ [{roll_str if roll != 20 or roll != 1 else ""}] 1d{dice_type} {modifier_line}')
        return messages


    async def parse_separate_dice(self, dice: str) -> tuple:
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


    async def matches_template(self, message):
        patterns = [
            r"([1-9]\d*)?d[1-9]\d*((\+|\-)([1-9]\d*)?d[0-9]\d*)*",  # Matches NdN+NdN+...+NdN, NdN, and dN where N > 0
            r"([1-9]\d*)?d[1-9]\d*((\+|\-)([1-9]\d*)?d[1-9]\d*)*(\+|\-)[0-9]\d*",  # Matches NdN+NdN+...+M, NdN+M, and dN+M
            r"[1-9]\d*#d[1-9]\d*((\+|\-)[0-9]\d*)?",  # Matches N#dN and N#dN+M where N > 0
        ]
        for i, pattern in enumerate(patterns):
            if re.fullmatch(pattern, message.replace(" ", "")):
                return i
        return None


    async def roll_dice(self, dice_type: int) -> int:
        return random.randint(1, dice_type)
    
        
    
    async def createFunCmdEmbed(self):
        em = discord.Embed(title = "Fun Commands", description = "These are the bot's Fun commands", color = discord.Colour.orange())
        em.set_thumbnail(url = EMBED_IMAGE)
        em.add_field(name = "Fun Commands", value = "Some Fun Bot Commands", inline = False)
        em.add_field(name = "/ping", value = "The bot replies with Pong!", inline = False)
        em.add_field(name = "/coinflip", value = "This command lets you flip a coin", inline = False)
        em.add_field(name = "/joke", value = "This command sends a random joke", inline = False)
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
        em.add_field(name = "/queue", value = "This command allows the user to view what songs are in queue!", inline = False)
        em.add_field(name = "/clear", value = "This command allows the user to clear the queue!", inline = False)
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
    


    async def get_score(self, interaction):
        #*Gets the user's score from the database
        score_query = "SELECT score FROM rps WHERE guild_id = ? AND user_id = ?"
        score = self.database.fetch_one_from_db(score_query, (interaction.guild.id, interaction.user.id))
        #*If there's no score, insert it into the database
        if not score:
            query = "INSERT INTO rps VALUES (?,?,?)"
            self.database.execute_db_query(query, (interaction.guild.id, interaction.user.id, 0))
            return 0
        else:
            return score

    
    async def determine_game_result(self, user_hand, bot_hand):
        #*Determines the result of the game
        if user_hand == bot_hand:
            return "It's a Draw!", discord.Colour.orange()
        if (user_hand == "✌️" and bot_hand == "🤜") or (user_hand == "✋" and bot_hand == "✌️") or (user_hand == "🤜" and bot_hand == "✋"):
            return "I won!", discord.Colour.red()
        return "You won!", discord.Colour.green()


    async def send_game_result(self, interaction, result, user_hand, bot_hand, score, color):
        embed = discord.Embed(title=result, description="Here's the result of the game", color=color)
        embed.add_field(name="You chose:", value=user_hand, inline=False)
        embed.add_field(name="I chose:", value=bot_hand, inline=False)
        embed.add_field(name="Score:", value=score, inline=False)
        await interaction.response.send_message(embed=embed)


    async def create_score_embed(self, score):
        em = discord.Embed(title="Your RPS Stats", description="These are your RPS Stats", color=discord.Colour.orange())
        em.add_field(name="Score:", value=score, inline=False)
        return em
    

    async def create_leaderboard_embed(self, scores):
        em = discord.Embed(title="RPS Leaderboard", description="These is the RPS Leaderboard", color=discord.Colour.orange())
        for score in scores:
            user = await self.bot.fetch_user(score[0])
            em.add_field(name=f"{user.display_name}", value=f"Score: {score[1]}", inline=False)
        return em
