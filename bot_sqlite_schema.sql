-- SQLite schema for Velox
-- Adapted from PostgreSQL schema with SQLite-specific modifications
--
-- Create levels table
CREATE TABLE levels (
    guild INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    level INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild, user_id)
);

-- Create twitch table
CREATE TABLE twitch (
    twitch_user TEXT NOT NULL,
    guild_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not live',
    PRIMARY KEY (twitch_user, guild_id)
);

-- Create levelsettings table
CREATE TABLE levelsettings (
    guild_id INTEGER PRIMARY KEY,
    levelsys INTEGER NOT NULL DEFAULT 0, -- BOOLEAN as INTEGER (0/1)
    role INTEGER,
    levelreq INTEGER,
    message TEXT
);

-- Create welcome table
CREATE TABLE welcome (
    guild_id INTEGER PRIMARY KEY,
    welcome_channel_id INTEGER,
    welcome_message TEXT,
    welcome_dm TEXT,
    welcome_gif_url TEXT
);

-- Create levelup table
CREATE TABLE levelup (
    guild_id INTEGER PRIMARY KEY,
    levelup_channel_id INTEGER
);

-- Create twitch_config table
CREATE TABLE twitch_config (
    guild_id INTEGER PRIMARY KEY,
    twitch_channel_id INTEGER
);

-- Create rps table
CREATE TABLE rps (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

-- Create defaultrole table
CREATE TABLE defaultrole (
    guild_id INTEGER PRIMARY KEY,
    role_id INTEGER
);

-- Create logsettings table
CREATE TABLE logsettings (
    guild_id INTEGER PRIMARY KEY,
    log_channel_id INTEGER,
    is_enabled INTEGER NOT NULL DEFAULT 0 -- BOOLEAN as INTEGER (0/1)
);

-- SQLite optimizations
-- Add indexes for common queries
CREATE INDEX idx_levels_guild ON levels(guild);
CREATE INDEX idx_levels_leaderboard ON levels(guild, level DESC, xp DESC);
CREATE INDEX idx_twitch_guild ON twitch(guild_id);

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;
