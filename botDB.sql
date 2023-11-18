CREATE TABLE IF NOT EXISTS levels (level INT, xp INT, user INT, guild INT);
CREATE TABLE IF NOT EXISTS twitch (twitch_user TEXT, status TEXT , guild_id INT);
CREATE TABLE IF NOT EXISTS levelsettings (levelsys BOOL, role INT, levelreq INT, message TEXT ,guild_id INT);
CREATE TABLE IF NOT EXISTS welcome (guild_id INT, welcome_channel_id INT);
CREATE TABLE IF NOT EXISTS levelup (guild_id INT, levelup_channel_id INT);
CREATE TABLE IF NOT EXISTS twitch_config (guild_id INT, twitch_channel_id INT);
CREATE TABLE IF NOT EXISTS rps (guild_id INT, user_id INT, score INT);
CREATE TABLE IF NOT EXISTS defaultrole (guild_id INT, role_id INT);