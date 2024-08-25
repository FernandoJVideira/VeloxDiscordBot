# Velox Discord Bot

An open-source discord bot made in Python and capable of running using Docker.

## Description

Velox bot is a general-purpose discord bot made in python. It is equiped with commands from moderation to playing music. It does so by connecting to a [Lavalink](https://github.com/lavalink-devs/Lavalink) server and using it to stream the songs. (And yes, it supports Youtube playback).

## Features

- Moderation Commands (Kick, Ban, Mute, etc)
- Server Edit Settings
- Leveling System
- Music Commands
- Fun Commands (RPS, Scream, Yell, Poll, etc)

## Installation

Head to [Discord Developer Portal](https://discord.com/developers/applications), login and create an application, then, head to the "Bot" section, copy the Bot's token and paste it in the DockerFile. Next you should head to [Twitch Developers](https://dev.twitch.tv/login), after login, register a new aplication as "Aplication Integration", following that, you'll want to copy the client id and client secret and paste them in the DockerFile as well as the auth token.

If you don't have a lavalink node to connect to, just follow the steps at the official [Lavalink](https://github.com/lavalink-devs/Lavalink) github repo and you'll be good to go.

Other option is to cd into the lavalink folder and run `docker-compose up -d`. That will run the lavalink server on a docker container on port 2333.

```
cd lavalink
docker-compose up -d
```

For this next phase, you'll have to get Docker installed and running on your machine.

No matter the OS, all you have to do is follow this steps:

```
git clone https://github.com/FernandoJVideira/VeloxDiscordBot.git
cd path_to_repo/VeloxDiscordBot
docker compose up -d
```

In case you don't want to run the bot using docker, install the requirements uncomenting the `python-dotenv==1.0.0` line in requirements.txt file and just uncomment the following lines in bot.py:

Run the following command:

```
pip install -r requirements.txt
```

Uncoment the following lines:

```
from dotenv import load_dotenv
load_dotenv("./vars.env")
```

and rename the _example.env_ file to _vars.env_ and paste the information there instead of using the provided docker compose file.

After that, edit the default values in lavalink/docker-compose.yml and lavalink/application.yml to your liking and run the lavalink server using the following command:

To edit the token and visitor data, you can use the following repository: [PoToken Generator](https://github.com/iv-org/youtube-trusted-session-generator)

```
cd lavalink
java -jar Lavalink.jar
```

Finally, run the bot using the following command:

```
python bot.py
```

(Also, this project is open for suggestions, so just leave them here or feel free to make pull requests :D)
