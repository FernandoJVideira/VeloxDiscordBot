import os
import random
import re
import discord
import requests
import sqlite3
from twitchAPI.twitch import Twitch
from discord.ext import commands, tasks
    

#* Connect to the database
database = sqlite3.connect("bot.db")
cursor = database.cursor()

#* Authentication with Twitch API. 
client_id = os.getenv("TWITCH_CLIENT_ID")
client_secret = os.getenv("TWITCH_CLIENT_SECRET")
twitch = Twitch(client_id, client_secret)
TWITCH_STREAM_API_ENDPOINT = "https://api.twitch.tv/helix/streams?user_id={}"
API_HEADERS = {
    'Authorization': 'Bearer ' + os.getenv("TWITCH_AUTH_TOKEN"),
    'Client-ID': client_id,
}

class EventHandler(commands.Cog):

    #* Constructor
    def __init__(self, bot):
        self.bot = bot

    #* Executed when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready for action!")
        await twitch.authenticate_app([])
        if not self.live_notifs_loop.is_running():
            self.live_notifs_loop.start()

    #* When the bot joins a guild, set the level system to disabled by default
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setLvlSysDefault(guild)
        await self.setDefaultWelcomeMessages(guild)

    #* When a member joins a guild, send a welcome message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guild_welcome_channel = await self.getChannel("welcome_channel_id", "welcome", guild.id)

        query = "SELECT role_id FROM defaultrole WHERE guild_id = ?"
        defaultrole = self.fetch_one_from_db(query, (guild.id,))
        
        await self.setDefaultRole(guild, member, defaultrole)

        dmchannel = await member.create_dm()
        query = "SELECT welcome_dm FROM welcome WHERE guild_id = ?"
        welcome_message = self.fetch_one_from_db(query, (guild.id,))
        if welcome_message:
            await dmchannel.send(welcome_message[0])

        if guild_welcome_channel:
            message_query = "SELECT welcome_message FROM welcome WHERE guild_id = ?"
            gif_query = "SELECT welcome_gif_url FROM welcome WHERE guild_id = ?"

            welcome_message = self.fetch_one_from_db(message_query, (guild.id,))
            welcome_gif = self.fetch_one_from_db(gif_query, (guild.id,))

            welcome_embed = await self.createEmbed(member,welcome_message[0], welcome_gif[0])
            await guild_welcome_channel.send(member.mention, embed=welcome_embed)

    #* When a message is sent, check if the level system is enabled, if so, add xp to the user
    @commands.Cog.listener()
    async def on_message(self, message):    
        await self.gain_xp(message)
        pattern_index = self.matches_template(message.content)
        if pattern_index is not None:
            match pattern_index:
                case 1 | 0:
                    text = await self.sum_rolled_dice(message.content)
                    await message.reply(text)                   
                case 2:
                    num_dice, dice_type, modifier, modifier_line = self.parse_separate_dice(message.content) 
                    messages = await self.roll_multiple_dice(num_dice, dice_type, modifier, modifier_line)
                    await message.reply('\n'.join(messages))
                
        await self.bot.process_commands(message)

    async def gain_xp(self, message):
        if message.author.bot:
            return
        author = message.author
        guild = message.guild
        
        level_up_channel = await self.getChannel("levelup_channel_id", "levelup", guild.id)        
        #* Get tge level system status
        query = "SELECT levelsys FROM levelsettings WHERE guild_id = ?"
        levelsys = self.fetch_one_from_db(query, (guild.id,))

        #* If the level system is disabled, return
        if levelsys and not levelsys[0]:
            return
        
        #* Get the user's xp and level
        xp, level = await self.getLvlXp(author, guild)

        #* Add xp to the user
        if level < 5:
            await self.setXp(xp, author, guild)
        else:
            rand = random.randint(1, (level//4))
            if rand == 1:
                await self.setXp(xp, author, guild)
        #* Check if the user has leveled up, if so, update the user's level and send a message
        if xp >= 100:
            level += 1
            #*Get the role reward, if any
            query = "SELECT role FROM levelsettings WHERE levelreq = ? AND guild_id = ?"
            role = self.fetch_one_from_db(query, (level,guild.id,))
            self.updateMemberLvl(author, guild, level)
            msg = await self.setLvlUpMsgTemplate(guild, author, level)
            #* Send the message and set the role reward, if any
            if role:
                await self.setLvlRoleReward(role[0], guild, msg, author, level, level_up_channel, message)
            if level_up_channel:
                await level_up_channel.send(msg)
            else:
                await message.channel.send(msg)

    @tasks.loop(seconds=30)
    async def live_notifs_loop(self):
        #* Gets all the guilds that have twitch streamers
        guilds_query = "SELECT guild_id FROM twitch"
        guilds = self.fetch_all_from_db(guilds_query, ())

        #* Checks if there are any guilds with twitch streamers
        if guilds is not None:
            for guild_id in guilds:
                #* Gets the guild, 'twitch streams' channel
                channel = await self.getChannel("twitch_channel_id", "twitch_config", guild_id[0])
                #* Gets all the streamers in the guild
                twitch_users = await self.getTwitchUsers(guild_id)

                #* For each streamer, check if they are live
                for twitch_user in twitch_users:
                    #* Get the streamer's status from the twitch API (used to compare with the status in the database)
                    status = await self.checkuser(twitch_user[0])
                    #* Get the streamer's status from the database
                    streamer_status = await self.getStreamerStatusDB(twitch_user, guild_id)

                    #* If the streamer is live
                    if status is True:
                        await self.sendNotificiation(streamer_status, channel, twitch_user)
                    else:
                        #* Update the streamer's status to not live
                        actual_status = 'not live'
                        await self.updateStreamerStatus(twitch_user[0], actual_status)  

#*------------------------------------------------------------------------------------------------------------*#UTILS#*------------------------------------------------------------------------------------------------------------*#

    """
    The function creates a welcome embed message with a personalized greeting and member information.
    
    :param member: The `member` parameter in the `createEmbed` function is an instance of the
    `discord.Member` class. It represents a member of a Discord server and contains information about
    that member, such as their name, discriminator, avatar, and ID
    :return: a discord.Embed object named "MyEmbed".
    """
    async def createEmbed(self, member, message, gif_url) -> discord.Embed:
        #* Welcome Embed
        embed = discord.Embed(
            title="👋 Welcome!", description=f"{member.mention}! {message}", color=discord.Colour.orange())
        embed.set_author(
            name=f"{member.name}", icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(
            url=f"{gif_url}")
        embed.set_footer(text=f"ID: {member.id}")

        return embed


    """
    The `getChannel` function retrieves a channel from the database based on the provided table row,
    table, and guild ID, and returns the channel if it exists, otherwise it returns None.
    
    :param tableRow: The `tableRow` parameter represents the column name in the database table from
    which you want to retrieve the channel ID
    :param table: The "table" parameter is the name of the table in the database from which you want to
    retrieve the channel
    :param guild_id: The `guild_id` parameter is the ID of the guild (server) that the channel belongs
    to
    :return: The function `getChannel` returns the channel object if it exists in the database and is
    found in the guild, otherwise it returns `None`.
    """
    async def getChannel(self, table_row, table, guild_id):
        #* Gets the given Channel from the database
        query = "SELECT " + table_row +" FROM "+ table +" WHERE guild_id = ?"
        channel_id = self.fetch_one_from_db(query, (guild_id,))

        #* Checks if the channel exists and returns it, if not, it returnd None
        if channel_id:
            #* Gets the guild and the channel
            guild = self.bot.get_guild(guild_id)
            channel = guild.get_channel(channel_id[0])
        else:
            channel = None
              
        return channel
    

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
                if part_dice_str and part_type_str:  # Check that both strings are not empty
                    part_dice, part_type = map(int, (part_dice_str, part_type_str))  # Convert the strings to integers
                    num_dice = part_dice
                    dice_type = part_type  # Assume all dice have the same type
            else:
                modifier = int(part)  # Convert the part to an integer and add it to the modifier

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
            r"([1-9]\d*)?d[1-9]\d*((\+|\-)([1-9]\d*)?d[1-9]\d*)*",  # Matches NdN+NdN+...+NdN, NdN, and dN where N > 0
            r"([1-9]\d*)?d[1-9]\d*((\+|\-)([1-9]\d*)?d[1-9]\d*)*(\+|\-)[1-9]\d*",  # Matches NdN+NdN+...+M, NdN+M, and dN+M
            r"[1-9]\d*#d[1-9]\d*((\+|\-)[1-9]\d*)?",  # Matches N#dN and N#dN+M where N > 0
        ]
        for i, pattern in enumerate(patterns):
            if re.fullmatch(pattern, message.replace(" ", "")):
                return i
        return None


    """
    The function sets a default role for a member in a guild, and if the bot doesn't have the necessary
    permissions, it prints an error message.
    
    :param guild: The "guild" parameter represents the Discord server or guild where the member is
    located. It is an object that contains information about the guild, such as its name, ID, and other
    properties
    :param member: The `member` parameter represents a member of a guild (server) in Discord. It could
    be an instance of the `discord.Member` class
    :param role: The `role` parameter is the ID of the role that you want to set as the default role for
    a member in a guild
    """
    async def setDefaultRole(self, guild, member, role):
        if role:
            #* Gets the guilds role
            default_role = guild.get_role(role[0])
            try:
                #* Adds the default role to the member
                await member.add_roles(default_role)
            except discord.HTTPException:
                print("I don't have the permissions to add the default role.") 


    """
    The function `getTwitchUsers` retrieves all Twitch users associated with a specific guild ID from a
    database.
    
    :param guild_id: The `guild_id` parameter is the ID of a guild or server in a chat platform, such as
    Discord. It is used to identify a specific server and retrieve the Twitch users associated with that
    server
    :return: the list of Twitch users associated with a specific guild ID.
    """
    async def getTwitchUsers(self, guild_id):
        twitch_query = "SELECT twitch_user FROM twitch WHERE guild_id = ?"
        twitch_users = self.fetch_all_from_db(twitch_query, (guild_id[0],))
        return twitch_users


    """
    The `checkuser` function checks if a Twitch user is currently live streaming and returns `True` if
    they are, `False` otherwise.
    
    :param user: The `user` parameter is the username of the Twitch user that you want to check if they
    are currently live streaming
    :return: The function `checkuser` returns a boolean value. It returns `True` if the Twitch user
    specified by the `user` parameter is currently live streaming, and `False` otherwise.
    """
    async def checkuser(self, user):
        try:
            #* Gets the twitch user's id and sends the request to the twitch API
            twitch_user_generator = twitch.get_users(logins=[user])
            twitch_user = await twitch_user_generator.__anext__()
            userid = twitch_user.id
            url = TWITCH_STREAM_API_ENDPOINT.format(userid)
            try:
                #* Gets the response from the twitch API and checks if the user is live, if not, returns false
                req = requests.Session().get(url, headers= API_HEADERS)
                jsondata = req.json()
                if jsondata['data'][0]['type'] == "live":
                    return True
                else:
                    return False
            except Exception:
                return False
        except StopAsyncIteration:
            return False
        

    """
    The function `getStreamerStatusDB` retrieves the status of a Twitch streamer from a database based
    on their username and guild ID.
    
    :param twitch_user: The `twitch_user` parameter is the username of the Twitch streamer that you want
    to check the status for. It is expected to be a string
    :param guild_id: The `guild_id` parameter is the unique identifier for a guild or server in a
    Discord bot. It is used to specify which guild's data is being queried or updated
    :return: the streamer status fetched from the database for a given Twitch user and guild ID.
    """
    async def getStreamerStatusDB(self, twitch_user, guild_id):
        status_query = "SELECT status FROM twitch WHERE twitch_user = ? AND guild_id = ?"
        streamer_status = self.fetch_one_from_db(status_query, (twitch_user[0], guild_id[0]))
        return streamer_status


    """
    The function updates the status of a Twitch streamer in a database.
    
    :param twitch_user: The `twitch_user` parameter is the username of the Twitch streamer whose status
    you want to update
    :param status: The status parameter is the new status that you want to update for the specified
    twitch_user
    """
    async def updateStreamerStatus(self, twitch_user, status):
        status_query = "UPDATE twitch SET status = ? WHERE twitch_user = ?"
        self.execute_db_query(status_query, (status, twitch_user))


    """
    The function sends a notification to a channel if a streamer's status is not live and updates the
    streamer's status to live.
    
    :param streamer_status: The `streamer_status` parameter is a list that contains the current status
    of the streamer. It is expected to have only one element, which can be either "not live" or "live"
    :param channel: The `channel` parameter is the channel or server where the notification will be
    sent. It is typically an object that represents a text channel in a Discord server
    :param twitch_user: The `twitch_user` parameter is a list that contains the Twitch username of the
    streamer
    """
    async def sendNotificiation(self, streamer_status, channel, twitch_user):
        #* Check if the streamer's status is not live
        if streamer_status[0] == 'not live':
            await channel.send(
                f":red_circle: **LIVE**\n @everyone is now streaming on Twitch!"
                f"\nhttps://www.twitch.tv/{twitch_user[0]}")
            #* Update the streamer's status to live
            actual_status = 'live'
            await self.updateStreamerStatus(twitch_user[0], actual_status)


    """
    The function `setLvlSysDefault` inserts default level settings into a database table for a specific
    guild.
    
    :param guild: The "guild" parameter is an object that represents a guild or server in a Discord bot.
    It typically contains information such as the guild's ID, name, members, channels, etc. In this
    case, it seems like the "guild" parameter is being used to identify the guild for which the
    """
    async def setLvlSysDefault(self, guild):
        lvlsys_query = "INSERT INTO levelsettings VALUES (?,?,?,?,?)"
        self.execute_db_query(lvlsys_query, (False,0,0,None,guild.id))

    """
    The function sets default welcome messages for a guild by inserting values into a database
    table.
    
    :param guild: The `guild` parameter represents a Discord server or guild. It is an object that
    contains information about the guild, such as its name, ID, and other properties. In this code
    snippet, the `guild` parameter is used to generate a welcome message that includes the guild's
    name
    """
    async def setDefaultWelcomeMessages(self, guild):
        welcome_message = f"Welcome to {guild.name}! Have fun!"
        welcome_gif = "https://media.giphy.com/media/61XS37iBats8J3QLwF/giphy.gif"
        welcome_query = "INSERT INTO welcome VALUES (?,?,?,?,?)"
        self.execute_db_query(welcome_query, (guild.id, None, welcome_message, welcome_message,welcome_gif))


    """
    The function `setLvlUpMsgTemplate` retrieves a level up message template from a database for a
    specific guild, and if there is no template, it sends a default level up message.
    
    :param guild: The `guild` parameter represents the Discord server or guild where the level up
    message is being set
    :param author: The `author` parameter refers to the user who leveled up. It is an object that
    represents the user in the Discord server
    :param level: The `level` parameter in the `setLvlUpMsgTemplate` function represents the level that
    the user has reached. It is used to customize the level up message by including the level number in
    the message
    :return: a message string. If there is a level up message template found in the database for the
    specified guild, it will be formatted with the author's mention and the level, and then returned. If
    there is no template found, a default level up message will be returned, mentioning the author and
    stating their new level.
    """
    async def setLvlUpMsgTemplate(self, guild, author, level):
        #* Get the level up message template from the database
        message_query = "SELECT message FROM levelsettings WHERE guild_id = ?"
        template = self.fetch_all_from_db(message_query, (guild.id,))

        #* Check if there is a template, if not, send the default message
        for message in template:
            #* If there is no template, send the default message
            if message[0] is not None:
                template = message[0]
                msg = template.format(user=author.mention, level=level)
                return msg
        msg = f"Congratulations {author.mention}, you have leveled up to level {level}!"
        return msg

    
    """
    The `getLvlXp` function retrieves a user's XP and level from a database, and if the user is not in
    the database, it adds them and sets their XP and level to 0.
    
    :param author: The `author` parameter represents the user for whom you want to retrieve the XP and
    level information. It is expected to be an object that represents a user in your application or bot
    :param guild: The "guild" parameter represents the guild (server) where the user is located. It is
    used to identify the specific guild in the database query and retrieve the user's XP and level
    information specific to that guild
    :return: The function `getLvlXp` returns the user's xp and level as a tuple.
    """
    async def getLvlXp(self, author, guild):
        #* Get the user's xp and level from the database
        xp_query = "SELECT xp FROM levels WHERE user = ? AND guild = ?"
        xp = self.fetch_one_from_db(xp_query, (author.id, guild.id))
        level_query = "SELECT level FROM levels WHERE user = ? AND guild = ?"
        level = self.fetch_one_from_db(level_query, (author.id, guild.id))

        #* If the user is not in the database, add them
        if not xp or not level:
            query = "INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)"
            self.execute_db_query(query, (0,0,author.id, guild.id))
        try:
            #* Get the user's xp and level
            xp = xp[0]
            level = level[0]
        except TypeError:
            #* If the user is not in the database, set their xp and level to 0
            xp = 0
            level = 0
        
        return xp, level


    """
    The function `setXp` adds a random amount of XP to a user and updates their XP in the database.
    
    :param xp: The `xp` parameter represents the current amount of experience points for the user
    :param author: The `author` parameter represents the user for whom the XP is being set. It is
    expected to be an object that contains information about the user, such as their ID, username, and
    other relevant details
    :param guild: The "guild" parameter represents the guild (server) where the user is located. It is
    used to identify the specific guild in the database query and update the user's XP accordingly
    """
    async def setXp(self, xp, author, guild):
        #* Add a random amount of xp to the user
        xp += random.randint(1, 3)
        #* Update the user's xp in the database
        xp_query = "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?"
        self.execute_db_query(xp_query, (xp, author.id, guild.id))


    """
    The function updates the level and XP of a member in a database.
    
    :param author: The "author" parameter refers to the user whose level is being updated. It is
    expected to be an object representing the user, typically obtained from a message or command context
    :param guild: The "guild" parameter refers to the guild or server where the user is a member. It is
    used to identify the specific guild in the database when updating the user's level
    :param level: The level parameter represents the new level that you want to update for the user
    """
    def updateMemberLvl(self, author, guild, level):
        #* Update the user's level in the database
        level_query = "UPDATE levels SET level = ? WHERE user = ? AND guild = ?"
        xp_query = "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?"
        self.execute_db_query(level_query, (level, author.id, guild.id))
        self.execute_db_query(xp_query, (0, author.id, guild.id))


    """
    The `setLvlRoleReward` function adds a specified role to a user and sends a message to a specified
    channel when the user levels up.
    
    :param role: The `role` parameter is the ID of the role that you want to assign to the user when
    they level up
    :param guild: The `guild` parameter represents the Discord server or guild where the role and user
    are located
    :param msg: The `msg` parameter is a string that represents the message to be sent when the user
    levels up. It can contain placeholders that will be replaced with the appropriate values
    :param author: The `author` parameter represents the user who leveled up
    :param level: The `level` parameter represents the level that the user has reached. It is used in
    the message to indicate the level that the user has leveled up to
    :param levelupChannel: The `levelupChannel` parameter is a channel object where the level up message
    will be sent. It is an optional parameter, meaning it can be `None` if there is no specific level up
    channel specified
    :param message: The `message` parameter is an instance of the `discord.Message` class. It represents
    the message that triggered the level up event
    :return: In this code, the `return` statement is used to exit the function and return control back
    to the caller. It is used after sending the appropriate messages or handling exceptions.
    """
    async def setLvlRoleReward(self, role, guild, msg, author, level, levelup_channel, message):
        #* Get the role from the guild
        role = guild.get_role(role)
        try:
            #* Add the role to the user
            await author.add_roles(role)
            #* Send the message to the level up channel, if any, if not, send it to the channel the user leveled up in
            if levelup_channel:
                await levelup_channel.send(msg + f" You have recieved the role {role.mention}!")
                return
            else:
                await message.channel.send(msg + f" You have recieved the role {role.mention}!")
                return
        #* If the bot doesn't have the permissions to add the role, send a message to the level up channel, if any, if not, send it to the channel the user leveled up in
        except discord.HTTPException:
            if levelup_channel:
                await levelup_channel.send(f"**{author.mention}** has leveled up to level **{level}**! They would have recieved the role {role.mention}, but I don't have the permissions to do so.")
                return
            else:
                await message.channel.send(f"**{author.mention}** has leveled up to level **{level}**! They would have recieved the role {role.mention}, but I don't have the permissions to do so.")
                return


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
    The function fetches one row from a database using a given query and parameters.
    
    :param query: The query parameter is a string that represents the SQL query you want to execute. It
    can be any valid SQL statement, such as a SELECT, INSERT, UPDATE, or DELETE statement
    :param params: The "params" parameter is a tuple that contains the values to be substituted into the
    query string. These values are used to replace the placeholders in the query string, if any
    :return: the result of the `fetchone()` method, which retrieves the next row from the result set
    returned by the `execute()` method.
    """
    def fetch_one_from_db(self, query, params):
        cursor.execute(query, params)
        return cursor.fetchone()
    

    """
    The function fetches all rows from a database using a given query and parameters.
    
    :param query: The query parameter is a string that represents the SQL query you want to execute. It
    can be any valid SQL statement, such as a SELECT, INSERT, UPDATE, or DELETE statement
    :param params: The "params" parameter is a tuple that contains the values to be substituted into the
    query string. These values are used to replace the placeholders in the query string, if any. The
    placeholders are typically represented by question marks (?) or percent signs (%s) in the query
    string
    :return: the result of the fetchall() method, which is a list of all the rows returned by the query
    execution.
    """
    def fetch_all_from_db(self, query, params):
        cursor.execute(query, params)
        return cursor.fetchall()

async def setup(bot) -> None:
    await bot.add_cog(EventHandler(bot))

