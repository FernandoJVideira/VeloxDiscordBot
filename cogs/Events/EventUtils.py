import random
import aiohttp
import discord
from discord.ext import commands, tasks
from cogs.DatabaseHandler import DatabaseHandler

class EventUtils:
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()

    #*Sets the status of the bot
    async def set_status(self):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"over {len(self.bot.guilds)} servers!"))

    #* Gets the given Channel from the database based on it's id
    async def get_channel(self, table_row, table, guild_id):
        #* Gets the given Channel from the database
        query = "SELECT " + table_row +" FROM "+ table +" WHERE guild_id = ?"
        channel_id = self.database.fetch_one_from_db(query, (guild_id,))

        #* Checks if the channel exists and returns it, if not, it returnd None
        if channel_id:
            #* Gets the guild and the channel
            guild = self.bot.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id[0])
            else:
                channel = None
        else:
            channel = None
        return channel
    
    #* Sets the default welcome message for the guild
    async def setDefaultWelcomeMessages(self, guild):
        welcome_message = f"Welcome to {guild.name}! Have fun!"
        welcome_gif = "https://media.giphy.com/media/XD9o33QG9BoMis7iM4/giphy.gif"
        welcome_query = "INSERT INTO welcome VALUES (?,?,?,?,?)"
        self.database.execute_db_query(welcome_query, (guild.id, None, welcome_message, welcome_message,welcome_gif))
    
    #* Builds the bot's welcome message embed
    async def create_welcome_embed(self, member, message, gif_url) -> discord.Embed:
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
    
    #* Sets the default role for the member when they join the server
    async def setDefaultRole(self, guild, member, role):
        if role:
            #* Gets the guilds role
            default_role = guild.get_role(role[0])
        else:
            return
        try:
            #* Adds the default role to the member
            await member.add_roles(default_role)
        except discord.HTTPException:
                #TODO: Add log message after implementing logger
                print("I don't have the permissions to add the default role.")  

    #* Gets all the added streamers from the database for a specific guild
    async def getTwitchUsers(self, guild_id):
        twitch_query = "SELECT twitch_user FROM twitch WHERE guild_id = ?"
        twitch_users = self.database.fetch_all_from_db(twitch_query, (guild_id[0],))
        return twitch_users
    
    #* Checks if a user is streaming on twitch
    async def checkIfUserIsStreaming(self, username):
        url = "https://gql.twitch.tv/gql"
        query = "query {\n  user(login: \""+username+"\") {\n    stream {\n      id\n    }\n  }\n}"
        async with aiohttp.ClientSession() as session:
            #TODO: Set the client id to the one from the .env file
            async with session.post(url, json={"query": query, "variables": {}}, headers={"client-id": "kimne78kx3ncx6brgo4mv6wki5h1ko"}) as response:
                data = await response.json()
                if data and "data" in data and data["data"] and "user" in data["data"] and data["data"]["user"]:
                    return data["data"]["user"]["stream"] is not None
                return False
            
    #* Gets the streamer's current status from the database
    async def getStreamerStatusDB(self, twitch_user, guild_id):
        status_query = "SELECT status FROM twitch WHERE twitch_user = ? AND guild_id = ?"
        streamer_status = self.database.fetch_one_from_db(status_query, (twitch_user[0], guild_id[0]))
        return streamer_status
        
    #* Updates the streamer's status in the database
    async def updateStreamerStatus(self, twitch_user, status):
        status_query = "UPDATE twitch SET status = ? WHERE twitch_user = ?"
        self.database.execute_db_query(status_query, (status, twitch_user))

    #* Sends the livestream notification to the channel
    async def sendNotificiation(self, streamer_status, channel, twitch_user):
        #* Check if the streamer's status is not live
        if streamer_status[0] == 'not live':
            await channel.send(
                f":red_circle: **LIVE**\n @everyone {twitch_user[0]} is now live on Twitch!"
                f"\n https://www.twitch.tv/{twitch_user[0]}")
            #* Update the streamer's status to live
            actual_status = 'live'
            await self.updateStreamerStatus(twitch_user[0], actual_status)
    
    #* Sets the default level system settings for the guild (disabled by default)
    async def setLvlSysDefault(self, guild):
        lvlsys_query = "INSERT INTO levelsettings VALUES (?,?,?,?,?)"
        self.database.execute_db_query(lvlsys_query, (False,0,0,None,guild.id))

    #* Sets the level up message template for the guild
    async def setDefaultLvlUpMsg(self, guild, author, level):
        #* Get the level up message template from the database
        message_query = "SELECT message FROM levelsettings WHERE guild_id = ?"
        template = self.database.fetch_all_from_db(message_query, (guild.id,))

        #* Check if there is a template, if not, send the default message
        for message in template:
            #* If there is no template, send the default message
            if message[0] is not None:
                template = message[0]
                msg = template.format(user=author.mention, level=level)
                return msg
        msg = f"Congratulations {author.mention}, you have leveled up to level {level}!"
        return msg
    
    #* Gets the user's xp and level from the database
    async def getLvlXp(self, author, guild):
        #* Get the user's xp and level from the database
        xp_query = "SELECT xp FROM levels WHERE user = ? AND guild = ?"
        xp = self.database.fetch_one_from_db(xp_query, (author.id, guild.id))
        level_query = "SELECT level FROM levels WHERE user = ? AND guild = ?"
        level = self.database.fetch_one_from_db(level_query, (author.id, guild.id))

        #* If the user is not in the database, add them
        if not xp or not level:
            query = "INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)"
            self.database.execute_db_query(query, (0,0,author.id, guild.id))
        try:
            #* Get the user's xp and level
            xp = xp[0]
            level = level[0]
        except TypeError:
            #* If the user is not in the database, set their xp and level to 0
            xp = 0
            level = 0
        
        return xp, level

    #* Sets the user's xp in the database
    async def setXp(self, xp, author, guild):
        #* Add a random amount of xp to the user
        xp += random.randint(1, 3)
        #* Update the user's xp in the database
        xp_query = "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?"
        self.database.execute_db_query(xp_query, (xp, author.id, guild.id))

    #* Updates the user's level in the database
    async def updateMemberLvl(self, author, guild, level):
        #* Update the user's level in the database
        level_query = "UPDATE levels SET level = ? WHERE user = ? AND guild = ?"
        xp_query = "UPDATE levels SET xp = ? WHERE user = ? AND guild = ?"
        self.database.execute_db_query(level_query, (level, author.id, guild.id))
        self.database.execute_db_query(xp_query, (0, author.id, guild.id))

    #* Sets the level up role reward for the user
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