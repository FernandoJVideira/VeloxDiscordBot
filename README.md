# Umbreon Discord Bot
An open-source discord bot made in Python and capable of running using Docker.

## Description
Umbreon bot is a general-purpose discord bot made in python. It is equiped with commands from moderation to playing music. It does so by connecting to a [Lavalink](https://github.com/lavalink-devs/Lavalink) server and using it to stream the songs. (And yes, it supports Youtube playback).

## Features

- Moderation Commands (Kick, Ban, Mute, etc)
- Server Edit Settings
- Leveling System
- Music Commands
- Fun Commands (RPS, Scream, Yell, Poll, etc)

## Installation
Head to [Discord Developer Portal](https://discord.com/developers/applications), login and create an application, then, head to the "Bot" section, copy the Bot's token and paste it in the DockerFile. Next you should head to [Twitch Developers](https://dev.twitch.tv/login), after login, register a new aplication as "Aplication Integration", following that, you'll want to copy the client id and client secret and paste them in the DockerFile as well as the auth token.

If you don't have a lavalink node to connect to, just follow the steps at the official [Lavalink](https://github.com/lavalink-devs/Lavalink) github repo and you'll be good to go. (My advice is to run both the bot and the lavalink server is the same machine but using Docker containers)

Next you'll need a [DockerHub](https://hub.docker.com) account to be able to upload and run the bot's immage.

For this next phase, you'll have to get Docker installed and running on your machine.

If you're using a Linux/Mac to build the docker image, all you have to do is follow this steps:

```
git clone https://github.com/FernandoJVideira/UmbreonBot.git
cd path_to_repo/UmbreonBot
docker-buildx build --platform <target_pc_platform> -t <your_docker_hub_username>/name_of_your_dockerhub_repo:latest --push
```
On windows: 

```
docker build --tag <image_name> .
docker image tag <image_name> <your_docker_hub_username>/<name_of_your_dockerhub_repo>
```

After that, go to your target machine, pull the bot's image from your DockerHub and run it in the same docker network as the Lavalink server.

In case you don't want to run the bot using docker, just uncomment the following lines in bot.py:

```
from dotenv import load_dotenv
load_dotenv("./vars.env")
```

and rename the _example.env_ file to _vars.env_ and paste the information there instead of using the provides DockerFile.

(Also, this project is open for suggestions, so just leave them here or feel free to make pull requests :D)