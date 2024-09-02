from datetime import datetime

class ModerationUtils:
    def __init__(self, bot):
        self.bot = bot

    async def find_banned_user(self, banlist, user_to_unban):
        for ban_entry in banlist:
            if user_to_unban == ban_entry.user.name:
                return ban_entry.user
        return None
    
    
    async def purge_messages_by_date(self, interaction, day, month, year):
        await interaction.channel.purge(after=datetime(year, month, day))


    async def purge_messages_by_limit(self, interaction, limit):
        await interaction.channel.purge(limit=int(limit) + 1)