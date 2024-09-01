import random
from discord.ext import commands, tasks
from cogs.DatabaseHandler import DatabaseHandler
from cogs.Events.EventUtils import EventUtils

class EventHandler(commands.Cog):

    #* Constructor
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()
        self.event_utils = EventUtils(bot)


    #* Executed when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready for action!")
        await self.event_utils.set_status()
        if not self.live_notifs_loop.is_running():
            self.live_notifs_loop.start()

    #* When the bot joins a guild, set the level system to disabled by default
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.event_utils.setLvlSysDefault(guild)
        await self.setDefaultWelcomeMessages(guild)
        await self.event_utils.set_status()

    #* When the bot leaves a guild, set the status to watching the amount of servers
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.event_utils.set_status()

    #* When a member joins a guild, send a welcome message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guild_welcome_channel = await self.event_utils.get_channel("welcome_channel_id", "welcome", guild.id)

        query = "SELECT role_id FROM defaultrole WHERE guild_id = ?"
        defaultrole = self.database.fetch_one_from_db(query, (guild.id,))
        
        await self.event_utils.setDefaultRole(guild, member, defaultrole)

        dmchannel = await member.create_dm()
        query = "SELECT welcome_dm FROM welcome WHERE guild_id = ?"
        welcome_message = self.database.fetch_one_from_db(query, (guild.id,))
        if welcome_message:
            await dmchannel.send(welcome_message[0])

        if guild_welcome_channel:
            message_query = "SELECT welcome_message FROM welcome WHERE guild_id = ?"
            gif_query = "SELECT welcome_gif_url FROM welcome WHERE guild_id = ?"

            welcome_message = self.database.fetch_one_from_db(message_query, (guild.id,))
            welcome_gif = self.database.fetch_one_from_db(gif_query, (guild.id,))

            welcome_embed = await self.event_utils.create_welcome_embed(member,welcome_message[0], welcome_gif[0])
            await guild_welcome_channel.send(member.mention, embed=welcome_embed)

    #* When a message is sent, check if the level system is enabled, if so, add xp to the user
    @commands.Cog.listener()
    async def on_message(self, message):    
        await self.gain_xp(message)                
        await self.bot.process_commands(message)

    async def gain_xp(self, message):
        if message.author.bot:
            return
        author = message.author
        guild = message.guild
        
        level_up_channel = await self.event_utils.get_channel("levelup_channel_id", "levelup", guild.id)        
        #* Get tge level system status
        query = "SELECT levelsys FROM levelsettings WHERE guild_id = ?"
        levelsys = self.database.fetch_one_from_db(query, (guild.id,))

        #* If the level system is disabled, return
        if not levelsys[0]:
            return
        
        #* Get the user's xp and level
        xp, level = await self.event_utils.getLvlXp(author, guild)

        #* Add xp to the user
        if level < 5:
            await self.event_utils.setXp(xp, author, guild)
        else:
            rand = random.randint(1, (level//4))
            if rand == 1:
                await self.event_utils.setXp(xp, author, guild)
        #* Check if the user has leveled up, if so, update the user's level and send a message
        if xp >= 100:
            level += 1
            #*Get the role reward, if any
            query = "SELECT role FROM levelsettings WHERE levelreq = ? AND guild_id = ?"
            role = self.database.fetch_one_from_db(query, (level,guild.id,))
            self.event_utils.updateMemberLvl(author, guild, level)
            msg = await self.event_utils.setDefaultLvlUpMsg(guild, author, level)
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
        guilds = self.database.fetch_all_from_db(guilds_query, ())

        #* Checks if there are any guilds with twitch streamers
        if guilds is not None:
            for guild_id in guilds:
                #* Gets the guild, 'twitch streams' channel
                channel = await self.event_utils.get_channel("twitch_channel_id", "twitch_config", guild_id[0])
                #* Gets all the streamers in the guild
                twitch_users = await self.event_utils.getTwitchUsers(guild_id)

                #* For each streamer, check if they are live
                for twitch_user in twitch_users:
                    #* Get the streamer's status from the twitch API (used to compare with the status in the database)
                    isLive = await self.event_utils.checkIfUserIsStreaming(twitch_user[0])
                    #* Get the streamer's status from the database
                    streamer_status = await self.event_utils.getStreamerStatusDB(twitch_user, guild_id)

                    #* If the streamer is live
                    if isLive is True:
                        await self.sendNotificiation(streamer_status, channel, twitch_user)
                    else:
                        #* Update the streamer's status to not live
                        actual_status = 'not live'
                        await self.event_utils.updateStreamerStatus(twitch_user[0], actual_status)  


async def setup(bot) -> None:
    await bot.add_cog(EventHandler(bot))

