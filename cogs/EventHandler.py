import os
import random
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

class eventHandler(commands.Cog):

    #*Constructor
    def __init__(self, bot):
        self.bot = bot

    #*executed when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready for action!")
        await twitch.authenticate_app([])
        if not self.live_notifs_loop.is_running():
            self.live_notifs_loop.start()

    #*When the bot joins a guild, set the level system to disabled by default
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setLvlSysDefault(guild)

    #*When a member joins a guild, send a welcome message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guildWelcomeChannel = await self.getChannel("welcome_channel_id", "welcome", guild.id)

        cursor.execute("SELECT role_id FROM defaultrole WHERE guild_id = ?", (guild.id,))
        defaultrole = cursor.fetchone()
        
        await self.setDefaultRole(guild, member, defaultrole)

        dmchannel = await member.create_dm()
        await dmchannel.send(f"Welcome to **{guild.name}**! Have fun!")

        if guildWelcomeChannel:
            MyEmbed = await self.createEmbed(member)
            await guildWelcomeChannel.send(member.mention, embed=MyEmbed)

    #*When a message is sent, check if the level system is enabled, if so, add xp to the user
    @commands.Cog.listener()
    async def on_message(self, message):    
        if message.author.bot:
            return
        author = message.author
        guild = message.guild
        
        levelUpChannel = await self.getChannel("levelup_channel_id", "levelup", guild.id)        
        #*Get tge level system status
        cursor.execute("SELECT levelsys FROM levelsettings WHERE guild_id = ?", (guild.id,))
        levelsys = cursor.fetchone()

        #*If the level system is disabled, return
        if levelsys and not levelsys[0]:
            return
        
        #*Get the user's xp and level
        xp, level = await self.getLvlXp(author, guild)

        #*Add xp to the user
        if level < 5:
            await self.setXp(xp, author, guild)
        else:
            rand = random.randint(1, (level//4))
            if rand == 1:
                await self.setXp(xp, author, guild)
        #*Check if the user has leveled up, if so, update the user's level and send a message
        if xp >= 100:
            level += 1
            #*Get the role reward, if any
            cursor.execute("SELECT role FROM levelsettings WHERE levelreq = ? AND guild_id = ?", (level,guild.id,))
            role = cursor.fetchone()
            self.updateMemberLvl(author, guild, level)
            msg = await self.setLvlUpMsgTemplate(guild, author, level)
            #*Send the message and set the role reward, if any
            if role:
                await self.setLvlRoleReward(role[0], guild, msg, author, level, levelUpChannel, message)
            if levelUpChannel:
                await levelUpChannel.send(msg)
            else:
                await message.channel.send(msg)

        await self.bot.process_commands(message)

    @tasks.loop(seconds=30)
    async def live_notifs_loop(self):
        #*Gets all the guilds that have twitch streamers
        guilds = cursor.execute("SELECT guild_id FROM twitch").fetchall()

        #*Checks if there are any guilds with twitch streamers
        if guilds is not None:
            for guild_id in guilds:
                #*Gets the guild, 'twitch streams' channel
                channel = await self.getChannel("twitch_channel_id", "twitch_config", guild_id[0])
                #*Gets all the streamers in the guild
                twitch_users = await self.getTwitchUsers(guild_id)

                #*For each streamer, check if they are live
                for twitch_user in twitch_users:
                    #*Get the streamer's status from the twitch API (used to compare with the status in the database)
                    status = await self.checkuser(twitch_user[0])
                    #*Get the streamer's status from the database
                    streamer_status = await self.getStreamerStatusDB(twitch_user, guild_id)

                    #*If the streamer is live
                    if status is True:
                        await self.sendNotificiation(streamer_status, channel, twitch_user)
                    else:
                        #*Update the streamer's status to not live
                        actualStatus = 'not live'
                        await self.updateStreamerStatus(twitch_user[0], actualStatus)  

#*------------------------------------------------------------------------------------------------------------*#UTILS#*------------------------------------------------------------------------------------------------------------*#

    async def createEmbed(self, member) -> discord.Embed:
        #*Welcome Embed
        MyEmbed = discord.Embed(
            title="👋 Welcomeee!", description=f"{member.mention}! Welcome to the Shit Showww!", color=discord.Colour.orange())
        MyEmbed.set_author(
            name=f"{member.name} #{member.discriminator}", icon_url=member.display_avatar.url)
        MyEmbed.set_thumbnail(url=member.display_avatar.url)
        MyEmbed.set_image(
            url="https://media.giphy.com/media/61XS37iBats8J3QLwF/giphy.gif")
        MyEmbed.set_footer(text=f"ID: {member.id}")

        return MyEmbed

    async def getChannel(self, tableRow, table, guild_id):
        #*Gets the given Channel from the database
        cursor.execute("SELECT " + tableRow +" FROM "+ table +" WHERE guild_id = ?", (guild_id,))
        channelID = cursor.fetchone()
        #*Checks if the channel exists and returns it, if not, it returnd None
        if channelID:
            #*Gets the guild and the channel
            guild = self.bot.get_guild(guild_id)
            channel = guild.get_channel(channelID[0])
        else:
            channel = None
              
        return channel

    #*Sets the default role for a member
    async def setDefaultRole(self, guild, member, role):
        if role:
            #*Gets the guilds role
            defaultRole = guild.get_role(role[0])
            try:
                #*Adds the default role to the member
                await member.add_roles(defaultRole)
            except discord.HTTPException:
                print("I don't have the permissions to add the default role.") 

    #*Returns all the twitch users in a guild
    async def getTwitchUsers(self, guild_id):
        twitch_users = cursor.execute("SELECT twitch_user FROM twitch WHERE guild_id = ?", (guild_id[0],))
        twitch_users = twitch_users.fetchall()
        return twitch_users

    #*Returns true if online, false if not.
    async def checkuser(self, user):
        try:
            #*Gets the twitch user's id and sends the request to the twitch API
            twitch_user_generator = twitch.get_users(logins=[user])
            twitch_user = await twitch_user_generator.__anext__()
            userid = twitch_user.id
            url = TWITCH_STREAM_API_ENDPOINT.format(userid)
            try:
                #*Gets the response from the twitch API and checks if the user is live, if not, returns false
                req = requests.Session().get(url, headers= API_HEADERS)
                jsondata = req.json()
                if jsondata['data'][0]['type'] == "live":
                    return True
                else:
                    return False
            except Exception as e:
                #*print("Error checking user: ", e)
                return False
        except StopAsyncIteration:
            return False
    #*Returns the streamer's status from the database for comparison
    async def getStreamerStatusDB(self, twitch_user, guild_id):
        streamer_status = cursor.execute("SELECT status FROM twitch WHERE twitch_user = ? AND guild_id = ?", (twitch_user[0], guild_id[0]))
        streamer_status = streamer_status.fetchone()
        return streamer_status

    #*Updates the streamer's status in the database according to the status from the twitch API
    async def updateStreamerStatus(self, twitch_user, status):
        cursor.execute("UPDATE twitch SET status = ? WHERE twitch_user = ?", (status, twitch_user))
        database.commit()

    #*Sends a notification to the guild's twitch channel
    async def sendNotificiation(self, streamer_status, channel, twitch_user):
        #*Check if the streamer's status is not live
        if streamer_status[0] == 'not live':
            await channel.send(
                f":red_circle: **LIVE**\n @everyone is now streaming on Twitch!"
                f"\nhttps://www.twitch.tv/{twitch_user[0]}")
            #*Update the streamer's status to live
            actualStatus = 'live'
            await self.updateStreamerStatus(twitch_user[0], actualStatus)

    #*Sets the level system to disabled by default
    async def setLvlSysDefault(self, guild):
        cursor.execute("INSERT INTO levelsettings VALUES (?,?,?,?,?)", (False,0,0,None,guild.id))
        database.commit() 

    #*Sets the level up message template
    async def setLvlUpMsgTemplate(self, guild, author, level):
        #*Get the level up message template from the database
        cursor.execute("SELECT message FROM levelsettings WHERE guild_id = ?", (guild.id,))
        template = cursor.fetchall()

        #*Check if there is a template, if not, send the default message
        for message in template:
            #*If there is no template, send the default message
            if message[0] is not None:
                template = message[0]
                msg = template.format(user=author.mention, level=level)
                return msg
        msg = f"Congratulations {author.mention}, you have leveled up to level {level}!"
        return msg

    #*Gets the user's xp and level
    async def getLvlXp(self, author, guild):
        #*Get the user's xp and level from the database
        xp = cursor.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id)).fetchone()
        level = cursor.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id)).fetchone()

        #*If the user is not in the database, add them
        if not xp or not level:
            cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)", (0,0,author.id, guild.id))
            database.commit()
        try:
            #*Get the user's xp and level
            xp = xp[0]
            level = level[0]
        except TypeError:
            #*If the user is not in the database, set their xp and level to 0
            xp = 0
            level = 0
        
        return xp, level

    #*Sets the user's xp
    async def setXp(self, xp, author, guild):
        #*Add a random amount of xp to the user
        xp += random.randint(1, 3)
        #*Update the user's xp in the database
        cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (xp, author.id, guild.id))
        database.commit()

    #*Updates the user's level
    def updateMemberLvl(self, author, guild, level):
        #*Update the user's level in the database
        cursor.execute("UPDATE levels SET level = ? WHERE user = ? AND guild = ?", (level, author.id, guild.id))
        cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (0, author.id, guild.id))
        database.commit()

    #*Sets the role reward, if any
    async def setLvlRoleReward(self, role, guild, msg, author, level, levelupChannel, message):
        #*Get the role from the guild
        role = guild.get_role(role)
        try:
            #*Add the role to the user
            await author.add_roles(role)
            #*Send the message to the level up channel, if any, if not, send it to the channel the user leveled up in
            if levelupChannel:
                await levelupChannel.send(msg + f" You have recieved the role {role.mention}!")
                return
            else:
                await message.channel.send(msg + f" You have recieved the role {role.mention}!")
                return
        #*If the bot doesn't have the permissions to add the role, send a message to the level up channel, if any, if not, send it to the channel the user leveled up in
        except discord.HTTPException:
            if levelupChannel:
                await levelupChannel.send(f"**{author.mention}** has leveled up to level **{level}**! They would have recieved the role {role.mention}, but I don't have the permissions to do so.")
                return
            else:
                await message.channel.send(f"**{author.mention}** has leveled up to level **{level}**! They would have recieved the role {role.mention}, but I don't have the permissions to do so.")
                return

async def setup(bot) -> None:
    await bot.add_cog(eventHandler(bot))

