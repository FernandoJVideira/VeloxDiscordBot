-- PostgreSQL schema for UmbreonBot2
-- Use BIGINT for Discord snowflakes, INT for smaller counters, BOOLEAN properly.

CREATE TABLE IF NOT EXISTS levels (
    guild BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    level INT NOT NULL DEFAULT 0,
    xp BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (guild, user_id)
);

CREATE TABLE IF NOT EXISTS twitch (
    twitch_user TEXT NOT NULL,
    guild_id BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not live',
    PRIMARY KEY (twitch_user, guild_id)
);

CREATE TABLE IF NOT EXISTS levelsettings (
    guild_id BIGINT PRIMARY KEY,
    levelsys BOOLEAN NOT NULL DEFAULT FALSE,
    role BIGINT,
    levelreq INT,
    message TEXT
);

CREATE TABLE IF NOT EXISTS welcome (
    guild_id BIGINT PRIMARY KEY,
    welcome_channel_id BIGINT,
    welcome_message TEXT,
    welcome_dm TEXT,
    welcome_gif_url TEXT
);

CREATE TABLE IF NOT EXISTS levelup (
    guild_id BIGINT PRIMARY KEY,
    levelup_channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS twitch_config (
    guild_id BIGINT PRIMARY KEY,
    twitch_channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS rps (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS defaultrole (
    guild_id BIGINT PRIMARY KEY,
    role_id BIGINT
);

CREATE TABLE IF NOT EXISTS logsettings (
    guild_id BIGINT PRIMARY KEY,
    log_channel_id BIGINT,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE
);

--
