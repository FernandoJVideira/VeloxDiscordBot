import random
import discord
from discord.ext import commands
import sqlite3

database = sqlite3.connect("bot.db")
cursor = database.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS levels (level INT, xp INT, user INT, guild INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS roles (level INT, role_name TEXT)")
cursor.execute("INSERT INTO roles VALUES (?,?)", (5, "Level 5"))
cursor.execute("INSERT INTO roles VALUES (?,?)", (10, "Level 10"))
cursor.execute("INSERT INTO roles VALUES (?,?)", (20, "Level 20"))
cursor.execute("INSERT INTO roles VALUES (?,?)", (30, "Level 30"))

database.commit()

class eventHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        guildchannelID = cursor.execute("SELECT welcome_channel_id FROM welcome WHERE guild_id = ?", (guild.id,)).fetchone()
        guildchannel = guild.get_channel(guildchannelID[0])

        dmchannel = await member.create_dm()
        await dmchannel.send(f"Welcome to **{guild.name}**! Have fun!")

        if guildchannel is not None:
            # Welcome Embed
            MyEmbed = discord.Embed(
                title="👋 Welcomeee!", description=f"{member.mention}! Welcome to the Shit Showww!", color=discord.Colour.orange())
            MyEmbed.set_author(
                name=f"{member.name} #{member.discriminator}", icon_url=member.display_avatar.url)
            MyEmbed.set_thumbnail(url=member.display_avatar.url)
            MyEmbed.set_image(
                url="https://media.giphy.com/media/61XS37iBats8J3QLwF/giphy.gif")
            MyEmbed.set_footer(text=f"ID: {member.id}")

            await guildchannel.send(member.mention, embed=MyEmbed)

    @commands.Cog.listener()
    async def on_message(self, message):
        
        if message.author.bot:
            return
        author = message.author
        guild = message.guild

        levelupChannelID = cursor.execute("SELECT levelup_channel_id FROM levelup WHERE guild_id = ?", (guild.id,)).fetchone()
        
        if levelupChannelID is not None:
            levelupChannel = guild.get_channel(levelupChannelID[0])
        
        xp = cursor.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id)).fetchone()
        level = cursor.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id)).fetchone()

        if not xp or not level:
            cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)", (0,0,author.id, guild.id))
            database.commit()
        try:
            xp = xp[0]
            level = level[0]
        except TypeError:
            xp = 0
            level = 0

        if level < 5:
            xp += random.randint(1, 3)
            #xp += 100
            cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (xp, author.id, guild.id))
            database.commit()
        else:
            rand = random.randint(1, (level//4))
            if rand == 1:
                xp += random.randint(1, 3)
                #xp += 100
                cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (xp, author.id, guild.id))
                database.commit()
        if xp >= 100:
            level += 1
            cursor.execute("UPDATE levels SET level = ? WHERE user = ? AND guild = ?", (level, author.id, guild.id))
            cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (0, author.id, guild.id))
            database.commit()

            if level == 5 or level == 10 or level == 20 or level == 30:
                await setLevelRole(guild, author, level)

            if levelupChannelID is not None:
                await levelupChannel.send(f"{author.mention} has leveled up to level **{level}**!")
            else:
                await message.channel.send(f"{author.mention} has leveled up to level **{level}**!")
        await self.bot.process_commands(message)


async def setLevelRole(guild, author, level):
    role_name = cursor.execute("SELECT role_name FROM roles WHERE level = ?", (level,)).fetchone()
    if role_name is not None:
        if discord.utils.get(guild.roles,name=role_name[0]) is None:
            roles = cursor.execute("SELECT role_name FROM roles",).fetchall()
            for role in roles:
                if discord.utils.get(guild.roles,name=role[0]) is None:
                    await guild.create_role(name=role[0], mentionable=False)
            role = discord.utils.get(guild.roles,name=role_name[0])
        else:
            role = discord.utils.get(guild.roles,name=role_name[0])
        
        if role is not None:
            await author.add_roles(role)
            return


async def setup(bot):
    await bot.add_cog(eventHandler(bot))
