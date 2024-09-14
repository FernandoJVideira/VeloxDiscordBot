from cogs.DatabaseHandler import DatabaseHandler

class BotConfigUtils:
    def __init__(self, database: DatabaseHandler):
        self.database = database

    async def checkStreamer(self, streamer):
        #* Fetches the streamer from the database
        query = "SELECT * FROM twitch WHERE twitch_user = ?"
    
        return self.database.fetch_one_from_db(query, (streamer,))