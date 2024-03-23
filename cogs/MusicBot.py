import datetime
import os
import discord
import asyncio
import wavelink
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

class Music(commands.Cog):

    #*Constructor
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.setup_hook())

    #*Setup hook
    async def setup_hook(self):
        #*Wait until the bot is ready
        await self.bot.wait_until_ready()
        #*Create the wavelink node
        #nodes = [wavelink.Node(uri=os.getenv('LAVALINK_HOST'), password=os.getenv('LAVALINK_PASSWORD'))]
        nodes = [wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')]
        #*Connect the node to the bot
        await wavelink.Pool.connect(nodes = nodes, client=self.bot, cache_capacity = 100)
        
    #*Events
    @commands.Cog.listener()
    #*When the wavelink node is ready
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.session_id} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player or player.queue.mode is wavelink.QueueMode.loop:
            return
        track: wavelink.Playable = payload.track
        embed: discord.Embed = await self.createEmbed(track, "Now Playing 🎵")
        await player.home.send(embed=embed)

    #*Commands
    #*Play command, plays a song in the voice channel
    @app_commands.command(name="play", description="Play a song in your voice channel.")
    @app_commands.describe(search="The song you want to play.")
    @app_commands.describe(source="The source of the song.")
    @app_commands.choices(source = [
        Choice(name = "Youtube", value = "youtube"),
        Choice(name = "SoundCloud", value = "soundcloud"),
        ])
    @app_commands.checks.has_role("DJ")
    async def play(self, ctx: discord.Interaction, search: str, source: str = None):
            await ctx.response.defer()

            if source == "youtube" or search.startswith("https://www.youtube.com/"):
                source = wavelink.TrackSource.YouTube
            elif source == "soundcloud" or search.startswith("https://soundcloud.com/"):
                source = wavelink.TrackSource.SoundCloud
            else:
                source = wavelink.TrackSource.YouTubeMusic

            #*Verify if the user is in a voice channel
            await self.checkVoiceChannel(ctx)
            
            #*Verify if the bot is in a voice channel and connect if not
            vc = await self.connectToChannel(ctx)
            vc.autoplay = wavelink.AutoPlayMode.partial

            #*Lock the player to this channel...
            if not hasattr(vc, "home"):
                vc.home = ctx.channel
            elif vc.home != ctx.channel:
                await ctx.followup.send(f"You can only play songs in {vc.home.mention}, as the player has already started there.")
                return

            #*Get the track and create the embed
            track = await self.getTrack(ctx, search, source)
            await vc.queue.put_wait(track)

            #*Play the song
            await asyncio.sleep(1)  #* wait for 1 second for the vc.is_playing() to be updated
            if not vc.playing and not vc.paused:
                await ctx.followup.send(f"Now Playing {track.name if isinstance(track, wavelink.Playlist) else track.title}")
                await self.playTrack(ctx, vc, track)
            else:
                queueEmbed = await self.createEmbed(track, "Added to queue 🎵")
                await ctx.followup.send(embed=queueEmbed)
 
    #*Pause command, pauses the current song
    @app_commands.command(name="pause", description="Pause/Unpauses the current song.")
    @app_commands.checks.has_role("DJ")
    async def pause(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.playing:
            await ctx.response.send_message("I am not playing anything.")
            return 
        #*Toggle the pause
        await vc.pause(not vc.paused)

        msg = "Paused" if vc.paused else "Unpaused"
        await ctx.response.send_message(f"{msg} the current song.")

    #*Skip command, skips the current song
    @app_commands.command(name="skip", description="Skips the current song.")
    @app_commands.checks.has_role("DJ")
    async def skip(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.playing:
            await ctx.response.send_message("I am not playing anything.")
            return 

        #*If not playing, stop the player
        await vc.skip(force=True)
        #*If the queue is empty, disable autoplay, else skip the song and continue
        if not vc.queue:
            await ctx.response.send_message("Skipped the current song. The queue is empty.")
        else:
            await ctx.response.send_message("Skipped the current song.")

    #*Queue command, shows the current queue
    @app_commands.command(name="queue", description="Shows the current queue.")
    async def queue(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.playing:
            await ctx.response.send_message("I am not playing anything.")
            return 
        #*Verify if the user is in a voice channel or in the same voice channel as the bot
        if not ctx.user.voice:
            await ctx.response.send_message("You must be in a voice channel to use this command.")
            return
        elif ctx.guild.voice_client and ctx.guild.voice_client.channel != ctx.user.voice.channel:
            await ctx.response.send_message("You must be in the same voice channel as the bot.")
            return
        #*If the queue is not empty, get the queue embed and send it
        if vc.queue:
            queueEm = await self.getQueueEmbed(vc)
            await ctx.response.send_message(embed=queueEm)
        else:
            #*If the queue is empty, send a message
            await ctx.response.send_message("The queue is empty.")
    
    #*Clear command, clears the current queue
    @app_commands.command(name="clear", description="Clears the current queue.")
    @app_commands.checks.has_role("DJ")
    async def clear(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.playing:
            await ctx.response.send_message("I am not playing anything.")
            return
        #*Clears the queue
        vc.queue.clear()
        await ctx.response.send_message("Cleared the queue.")

    #*Disconnect command, disconnects the bot from the voice channel
    @app_commands.command(name="leave", description="Disconnects the bot from the voice channel.")
    @app_commands.checks.has_role("DJ")
    async def disconnect(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc:
            await ctx.response.send_message("I am not connected to a voice channel.")
            return
        #*Disconnects the bot from the voice channel
        await vc.disconnect()
        await ctx.response.send_message("Disconnected from the voice channel.")
    
    @app_commands.command(name="loop", description="Loops the current song.")
    @app_commands.checks.has_role("DJ")
    async def loop(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.playing:
            await ctx.response.send_message("I am not playing anything.")
            return
        #*Loops the current song
        if vc.queue.mode is wavelink.QueueMode.loop:
            vc.queue.mode = wavelink.QueueMode.normal
            await ctx.response.send_message("Looping is now disabled.")
        else:
            vc.queue.mode = wavelink.QueueMode.loop
            await ctx.response.send_message("Looping is now enabled.")

    @app_commands.command(name="queueloop", description="Loops the queue.")
    @app_commands.checks.has_role("DJ")
    async def queueLoop(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.playing:
            await ctx.response.send_message("I am not playing anything.")
            return
        #*Loops the current queue
        if vc.queue.mode is wavelink.QueueMode.loop_all:
            vc.queue.mode = wavelink.QueueMode.normal
            await ctx.response.send_message("Queue Looping is now disabled.")
        else:
            vc.queue.mode = wavelink.QueueMode.loop_all
            await ctx.response.send_message("Queue Looping is now enabled.")

    #*Error Handling, these functions are called when an error occurs sending a message to the user

    @play.error
    async def play_error(self, ctx: discord.Interaction, error):
        # Check if the interaction is still valid
        if not ctx.response.is_done():
            if isinstance(error, app_commands.errors.MissingRole):
                await ctx.response.send_message("You must have the DJ role to use this command.")
            else:
                await ctx.response.send_message("Invalid search query.")
                print(error)
        else:
            print("The interaction is no longer valid.")

    @pause.error
    async def pause_error(self, ctx: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        else:
            await ctx.response.send_message("An unknown error occured.")
    @skip.error 
    async def skip_error(self, ctx: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        else:
            await ctx.response.send_message("An unknown error occured.")
            print(error)
    
    @loop.error
    async def loop_error(self, ctx: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        else:
            await ctx.response.send_message("An unknown error occured.")

    @queue.error
    async def queue_error(self, ctx: discord.Interaction, error):
        await ctx.response.send_message("An unknown error occured.")
        print(error.args)

    @disconnect.error
    async def disconnect_error(self, ctx: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        else:
            await ctx.response.send_message("An unknown error occured.")


    #*Utility Functions
    """
    The function "checkVoiceChannel" checks if the user is in a voice channel or in the same voice
    channel as the bot, and sends an appropriate message if not.
    
    :param ctx: The parameter `ctx` is of type `discord.Interaction`, which represents an interaction
    with a Discord bot. It contains information about the user, the guild, and the voice channel
    :type ctx: discord.Interaction
    :return: if the user is not in a voice channel or not in the same voice channel as the bot.
    """
    async def checkVoiceChannel(self, ctx: discord.Interaction):
        #*Verify if the user is in a voice channel or in the same voice channel as the bot
        if not ctx.user.voice:
            await ctx.response.send_message("You must be in a voice channel to use this command.")
            return
        elif ctx.guild.voice_client and ctx.guild.voice_client.channel != ctx.user.voice.channel:
            await ctx.response.send_message("You must be in the same voice channel as the bot.")
            return
        
    """
    The function `connectToChannel` connects the bot to a voice channel if it is not already connected.
    
    :param ctx: The parameter `ctx` is of type `discord.Interaction`, which represents the context of
    the interaction with the bot. It contains information about the user, the guild, and the channel
    where the interaction occurred
    :type ctx: discord.Interaction
    :return: a wavelink.Player object, which represents the voice client that the bot is connected to.
    """
    async def connectToChannel(self, ctx: discord.Interaction):
        #*Verify if the bot is in a voice channel and connect if not
        if not ctx.guild.voice_client:
            vc: wavelink.Player = await ctx.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        else:
            vc: wavelink.Player = ctx.guild.voice_client
        return vc
    

    """
    The `getTrack` function searches for a track or playlist based on the given search query and returns
    the track and an embed message.
    
    :param ctx: The parameter `ctx` is of type `discord.Interaction`, which represents the context of
    the interaction with the Discord API. It contains information about the user, the channel, and the
    server where the interaction occurred
    :type ctx: discord.Interaction
    :param search: The `search` parameter is a string that represents the query used to search for a
    track or playlist. It is used to search for either a specific song or a playlist on YouTube
    :type search: str
    :return: The function `getTrack` returns two values: `track` and `musicEmbed`.
    """
    async def getTrack(self, ctx: discord.Interaction, search: str, source : wavelink.enums.TrackSource):
        #*If a playlist is searched, search for the playlist, else search for the song
        tracks: wavelink.Search = await wavelink.Playable.search(search, source=source)
        if not tracks:
            await ctx.response.send_message(f'No tracks found with query: `{search}`')
            return

        if not isinstance(tracks, wavelink.Playlist):
            tracks: wavelink.Playable = tracks[0]
        return tracks
    
    async def createEmbed(self, track, embedTitle):
        #*If a playlist is searched, the enbed will have a different format and it's title will be the playlist name, else the embed will have a different format and it's title will be the song title
        em = discord.Embed(title=f"{embedTitle}", description=f"{track.title} by {track.author}", color=discord.Color.orange())
        #*These fields are only added if the track is not a playlist
        if track.artwork:
            em.set_thumbnail(url=track.artwork)
            em.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=track.length)))
        return em
    

    """
    This function plays a track in a voice channel using a music player and handles playlist management.
    
    :param ctx: The `ctx` parameter is of type `discord.Interaction` and represents the context of the
    interaction, such as the user and the channel where the interaction occurred
    :type ctx: discord.Interaction
    :param vc: The parameter `vc` is of type `wavelink.Player`, which is a player object used for
    playing audio tracks in a voice channel
    :type vc: wavelink.Player
    :param track: The `track` parameter in the `playTrack` function is the track that you want to play.
    It can be either a single song or a playlist
    :param musicEmbed: The `musicEmbed` parameter is an embed object that contains information about the
    track that is being played. It is sent as a message in the Discord channel using the `send_message`
    method of the `ctx.response` object. The embed typically includes details such as the track title,
    artist, duration
    :return: nothing (None).
    """
    async def playTrack(self, ctx: discord.Interaction, vc: wavelink.Player, tracks):
        #*Play the track from the queue
        await vc.play(vc.queue.get())
    
    
    """
    The `getQueueEmbed` function takes a voice client and returns an embed containing the queue of songs
    with their titles and durations.
    
    :param vc: The parameter `vc` is of type `wavelink.Player`. It represents the voice client or player
    object that is used to control the audio playback
    :type vc: wavelink.Player
    :return: an instance of the `discord.Embed` class, which represents an embedded message in Discord.
    """
    async def getQueueEmbed(self, vc: wavelink.Player):
        #*Set a counter and a list of songs
        songCounter = 0
        songs = []
        em = discord.Embed(title="Queue (First 25 Songs added)", color=discord.Color.orange())
        #*Add the songs to the list and adds fields to the embed
        for song in vc.queue:
            if songCounter >= 25:
                break
            songCounter += 1
            songs.append(f"{songCounter}. {song}")
            em.add_field(name=f"{songCounter} - {song.title}", value=f"Duration: {str(datetime.timedelta(milliseconds=song.length))}", inline=False)
        return em
            
async def setup(bot):
    await bot.add_cog(Music(bot))