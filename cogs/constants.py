# Cog Loading
EXTENTIONS = [
    "cogs.Commands.Sync", 
    "cogs.Events.EventHandler", 
    "cogs.Commands.Music.Music", 
    "cogs.Commands.Fun.FunCommands",
    "cogs.Commands.LevelSys.LevelSysConfig",
    "cogs.Commands.LevelSys.LevelSysCommands",
    "cogs.Commands.Moderation.ModerationCommands",
    "cogs.Commands.ServerConfig.ServerConfigCommands",
    "cogs.Commands.Config.BotConfig",
]

# Database
DB_FILE = "botDB.sql"
DB_PATH = "bot.db"

# Messages
NO_PERMS_MESSAGE = "You don't have permission to do that!"
LVLSYS_DISABLED = "The Leveling System is disabled in this server!"

# URLs
EMBED_IMAGE = "https://th.bing.com/th/id/OIG3.1SD.1zAEYXWKZqiWkNOc?pid=ImgGn"
API_URL = "https://v2.jokeapi.dev/"
JOKE_TYPES = ["Programming", "Miscellaneous", "Dark", "Pun", "Spooky", "Christmas"]

# Database Queries
LEVELSYS_QUERY = "SELECT levelsys FROM levelsettings WHERE guild_id = ?"
LVLSYS_INSERT_QUERY = "INSERT INTO levelsettings VALUES (?,?,?,?,?)"

# Music
NOT_PLAYING_MESSAGE = "I am not playing any music."
UNKNOWN_ERROR_MESSAGE = "An unknown error occured."
ROLE_REQUIRED_MESSAGE = "You must have the DJ role to use this command."