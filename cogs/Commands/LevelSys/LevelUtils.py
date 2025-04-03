import discord
from cogs.DatabaseHandler import DatabaseHandler
from easy_pil import Canvas, Font, Editor, load_image_async


class LevelUtils:

    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseHandler()
    
    #*Gets the user's xp and level from the database
    async def getLvlAndXp(self, member, guild):
        xp_query = "SELECT xp FROM levels WHERE user = ? AND guild = ?"
        xp = self.database.fetch_one_from_db(xp_query, (member.id, guild.id))
        level_query = "SELECT level FROM levels WHERE user = ? AND guild = ?"
        level = self.database.fetch_one_from_db(level_query, (member.id, guild.id))
        #*If there's no xp or level, insert it into the database and return 0 for each
        if not xp or not level:
            query = "INSERT INTO levels (level, xp, user, guild) VALUES (?,?,?,?)"
            self.database.execute_db_query(query, (0,0,member.id, guild.id))
            return 0, 0
        #*Return the xp and level
        xp = xp[0]
        level = level[0]
        return xp, level


    #*Creates a rank image for the user
    async def createRankImage(self,member, user_data):
        #*Create a background image
        background = Editor(Canvas((900, 300), color="#141414"))
        #*Load the user's profile picture, resize it and make it a circle
        profile_picture = await load_image_async(str(member.avatar.url))
        profile = Editor(profile_picture).resize((150, 150)).circle_image()

        #*Set the font used for the text
        poppins = Font.poppins(size=40)
        poppins_small = Font.poppins(size=30)

        #*Create the shapes for the card
        card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]

        #*Create the card
        background.polygon(card_right_shape, color="#FFFFFF")
        background.paste(profile, (30,30))
        background.rectangle((30, 220), width=650, height=40, color="#FFFFFF", radius=20)
        background.bar((30, 220), max_width=650, height=40, percentage=user_data["precentage"], color="#282828", radius=20)
        background.text((200, 40), user_data["name"], font=poppins, color="#FFFFFF")
        background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
        background.text((200, 130), f"Level - {user_data['level']} | XP - {int(user_data['xp'])}%", font=poppins_small, color="#FFFFFF")

        #*Return the image as a file
        file = discord.File(fp=background.image_bytes, filename="levelcard.png")

        return file


    #*Creates an embed with the role rewards for each level
    async def createRoleRewardsEmbed(self, interaction : discord.Interaction, role_rewards):
        #*Create the embed
        em = discord.Embed(title="Rewards", description="These are the rewards for each level", color=discord.Colour.orange())
        #*Add the rewards to the embed
        for role in role_rewards:
            role_obj = interaction.guild.get_role(role[1])
            role_name = role_obj.mention if role_obj else "Role not found"
            em.add_field(name=f"Level {role[2]}", value=role_name, inline=False)
        return em
    

    #*Creates a guild level leaderboard embed
    async def createLevelLeaderBoardEmbed(self,data,interaction):
        #*Gets the number of users in the server
        users_count = len(data)
        #*Creates the embed
        em = discord.Embed(title="Leaderboard", description=f"These are the top {users_count} users in the server", color=discord.Colour.orange())
        #* The enumerate function is used to get the index and user data in the loop
        for index, user_data in enumerate(data, start=1):
            user = interaction.guild.get_member(user_data[2])
            
            if not user:
                continue

            field_name = f"{index}. {user.display_name}"
            field_value = f"Level: **{user_data[0]}** | XP: **{user_data[1]}**"
            em.add_field(name=field_name, value=field_value, inline=False)
        return em
