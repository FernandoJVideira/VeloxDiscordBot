import datetime
import os
import discord
import asyncio
import wavelink
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from cogs.UI import ButtonView

NOT_PLAYING_MESSAGE = "I am not playing any music."
UNKNOWN_ERROR_MESSAGE = "An unknown error occured."
ROLE_REQUIRED_MESSAGE = "You must have the DJ role to use this command."

class Music(commands.Cog):

    #*Constructor
    def __init__(self, bot):
        self.bot = bot
        
    #* Setup hooks
    #* 
    async def cog_load(self) -> None:
        #*Create the wavelink node
        nodes = [wavelink.Node(uri=os.getenv('LAVALINK_HOST'), password=os.getenv('LAVALINK_PASSWORD'))]
        #*Connect the node to the bot
        await wavelink.Pool.connect(nodes = nodes, client=self.bot, cache_capacity = 100)
        
    #* Events
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
        await player.home.send(embed=embed, view=ButtonView(self))

    #* Commands
    #* Play command, plays a song in the voice channel
    @app_commands.command(name="play", description="Play a song in your voice channel.")
    @app_commands.describe(search="The song you want to play.")
    @app_commands.describe(source="The source of the song.")
    @app_commands.choices(source = [
        Choice(name = "Youtube Music", value = "ytmusic"),
        Choice(name = "SoundCloud", value = "soundcloud"),
        ])
    async def play(self, interaction: discord.Interaction, search: str, source: str = None):
        #* Verify if the user is in a voice channel
        if not await self.checkVoiceChannel(interaction) or not await self.checkDJRole(interaction):
            return
        
        #* Defer the bot's response
        await interaction.response.defer()

        #* Get the source of the song based on the search query or the source parameter
        source = await self.checkURL(interaction, search) if source is None else await self.getSource(source)
        
        #* Verify if the bot is in a voice channel and connect if not
        vc = await self.connectToChannel(interaction)
        vc.autoplay = wavelink.AutoPlayMode.partial

        #* Lock the player to this channel...
        if not hasattr(vc, "home"):
            vc.home = interaction.channel
        elif vc.home != interaction.channel:
            await interaction.followup.send(f"You can only play songs in {vc.home.mention}, as the player has already started there.")
            return

        #* Get the track and create the embed
        track = await self.getTrack(interaction, search, source)
        await vc.queue.put_wait(track)

        #* Play the song
        await asyncio.sleep(1)  #* wait for 1 second for the vc.is_playing() to be updated
        if not vc.playing and not vc.paused:
            await interaction.followup.send(f"Now Playing {track.name if isinstance(track, wavelink.Playlist) else track.title}")
            await self.playTrack(interaction, vc, track)
        else:
            queue_embed = await self.createEmbed(track, "Added to queue 🎵")
            await interaction.followup.send(embed=queue_embed)
 
    async def pause(self, interaction: discord.Interaction):
        if not await self.checkVoiceChannel(interaction):
            return
        if not await self.checkDJRole(interaction):
            return
        #* Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message(NOT_PLAYING_MESSAGE)
            return 
        #* Toggle the pause
        await vc.pause(not vc.paused)

        msg = "Paused" if vc.paused else "Unpaused"
        await interaction.response.send_message(f"{msg} the current song.", ephemeral=True, delete_after=5)

    #* Skip command, skips the current song
    async def skip(self, interaction: discord.Interaction):
        if not await self.checkDJRole(interaction):
            return
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message(NOT_PLAYING_MESSAGE, ephemeral=True, delete_after=5)
            return 
        elif vc.queue.mode != wavelink.QueueMode.normal:
            vc.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("Looping is now disabled.", ephemeral=True, delete_after=5)
            return
        #* If not playing, stop the player
        await vc.skip(force=True)
        #* If the queue is empty, disable autoplay, else skip the song and continue
        if not vc.queue:
            await interaction.response.send_message("Skipped the current song. The queue is empty.", ephemeral=True, delete_after=5)
        else:
            await interaction.response.send_message("Skipped the current song.", ephemeral=True, delete_after=5)

    #* Queue command, shows the current queue
    @app_commands.command(name="queue", description="Shows the current queue.")
    async def queue(self, interaction: discord.Interaction):
        #* Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message(NOT_PLAYING_MESSAGE, ephemeral=True, delete_after=5)
            return 
        if not await self.checkVoiceChannel(interaction):
            return
        #* If the queue is not empty, get the queue embed and send it
        if vc.queue:
            queue_em = await self.getQueueEmbed(vc)
            await interaction.response.send_message(embed=queue_em)
        else:
            #* If the queue is empty, send a message
            await interaction.response.send_message("The queue is empty.", ephemeral=True, delete_after=5)
    
    #* Clear command, clears the current queue
    @app_commands.command(name="clear", description="Clears the current queue.")
    @app_commands.checks.has_role("DJ")
    async def clear(self, interaction: discord.Interaction):
        #* Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message(NOT_PLAYING_MESSAGE, ephemeral=True, delete_after=5)
            return
        #* Clears the queue
        vc.queue.clear()
        await interaction.response.send_message("Cleared the queue.", ephemeral=True, delete_after=5)

    #* Disconnect command, disconnects the bot from the voice channel
    async def disconnect(self, interaction: discord.Interaction):
        if not await self.checkDJRole(interaction):
            return
        #* Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("I am not connected to a voice channel.", ephemeral=True, delete_after=5)
            return
        #* Disconnects the bot from the voice channel
        await vc.disconnect()
        await interaction.response.send_message("Disconnected from the voice channel.", ephemeral=True, delete_after=5)

    async def loop(self, interaction: discord.Interaction):
        if not await self.checkDJRole(interaction):
            return
        #* Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message(NOT_PLAYING_MESSAGE, ephemeral=True, delete_after=5)
            return
        #* Loops the current song
        if vc.queue.mode is wavelink.QueueMode.loop:
            vc.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("Looping is now disabled.", ephemeral=True, delete_after=5)
        else:
            vc.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("Looping is now enabled.", ephemeral=True, delete_after=5)

    async def queueLoop(self, interaction: discord.Interaction):
        if not await self.checkDJRole(interaction):
            return
        #* Gets the voice client and checks if it is playing
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message(NOT_PLAYING_MESSAGE, ephemeral=True, delete_after=5)
            return
        #* Loops the current queue
        if vc.queue.mode is wavelink.QueueMode.loop_all:
            vc.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("Queue Looping is now disabled.", ephemeral=True, delete_after=5)
        else:
            vc.queue.mode = wavelink.QueueMode.loop_all
            await interaction.response.send_message("Queue Looping is now enabled.", ephemeral=True, delete_after=5)


    #* Error Handling, these functions are called when an error occurs sending a message to the user
    @play.error
    async def play_error(self, interaction: discord.Interaction, error):
        # Check if the interaction is still valid
        if not interaction.response.is_done():
            if isinstance(error, app_commands.errors.MissingRole):
                await interaction.response.send_message(ROLE_REQUIRED_MESSAGE, ephemeral=True, delete_after=5)
            else:
                await interaction.response.send_message("Invalid search query.", ephemeral=True, delete_after=5)
                print(error)
        else:
            print("The interaction is no longer valid.")

    @queue.error
    async def queue_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(UNKNOWN_ERROR_MESSAGE, ephemeral=True, delete_after=5)
        print(error.args)



    #*Utility Functions
    async def checkDJRole(self, interaction: discord.Interaction):
        if not "DJ" in [role.name for role in interaction.user.roles]:
            await interaction.response.send_message("You must have the DJ role to use this command.", ephemeral=True, delete_after=5)
            return False
        return True
    """
    The function "checkVoiceChannel" checks if the user is in a voice channel or in the same voice
    channel as the bot, and sends an appropriate message if not.
    
    :param interaction: The parameter `interaction` is of type `discord.Interaction`, which represents an interaction
    with a Discord bot. It contains information about the user, the guild, and the voice channel
    :type interaction: discord.Interaction
    :return: if the user is not in a voice channel or not in the same voice channel as the bot.
    """
    async def checkVoiceChannel(self, interaction: discord.Interaction):
         #* Verify if the user is in a voice channel or in the same voice channel as the bot
        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True, delete_after=5)
            return False
        elif interaction.guild.voice_client and interaction.guild.voice_client.channel != interaction.user.voice.channel:
            await interaction.response.send_message("You must be in the same voice channel as the bot.", ephemeral=True, delete_after=5)
            return False
        return True
        
    """
    The function `connectToChannel` connects the bot to a voice channel if it is not already connected.
    
    :param interaction: The parameter `interaction` is of type `discord.Interaction`, which represents the context of
    the interaction with the bot. It contains information about the user, the guild, and the channel
    where the interaction occurred
    :type interaction: discord.Interaction
    :return: a wavelink.Player object, which represents the voice client that the bot is connected to.
    """
    async def connectToChannel(self, interaction: discord.Interaction):
        #*Verify if the bot is in a voice channel and connect if not
        if not interaction.guild.voice_client:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        else:
            vc: wavelink.Player = interaction.guild.voice_client
        return vc
    
    """
        The function `checkURL` checks if a given search query is a URL and returns
        the corresponding source type for music streaming services.
        
        :param interaction: The `interaction` parameter in your function represents the context of
        the interaction in Discord. It contains information about the user, the
        channel, and the server where the interaction took place. In this case, it
        is of type `discord.Interaction`, which is a class representing an
        interaction with a bot in
        :type interaction: discord.Interaction
        :param search: The `search` parameter in the `checkURL` function is a string
        that represents the search query or URL that the function will check to
        determine its source type (YouTube, SoundCloud, YouTube Music). The function
        checks the `search` string to see if it starts with specific prefixes
        corresponding to different
        :type search: str
        :return: a specific type of source based on the URL provided in the `search`
        parameter. If the URL starts with "https://youtu", it returns
        `wavelink.TrackSource.YouTube`. If it starts with "https://soundcloud", it
        returns `wavelink.TrackSource.SoundCloud`. If it starts with
        "https://music.youtube", it returns `wavelink.Track
    """
    async def checkURL(self,interaction:discord.Interaction ,search: str):
        #*Check if the search query is a URL
        if search.startswith("https://youtu"):
            return wavelink.TrackSource.YouTube
        elif search.startswith("https://soundcloud"):
            return wavelink.TrackSource.SoundCloud
        elif search.startswith("https://music.youtube"):
            return wavelink.TrackSource.YouTubeMusic
        else:
            return wavelink.TrackSource.YouTube


    """
        The function `getSource` returns the appropriate track source based on the
        input string "ytmusic", "soundcloud", or defaulting to "YouTube".
        
        :param source: The `getSource` method is an asynchronous function that takes
        a `source` parameter of type `str`. Depending on the value of the `source`
        parameter, the function returns a corresponding `wavelink.TrackSource` enum
        value
        :type source: str
        :return: The function `getSource` returns a `wavelink.TrackSource` based on
        the input `source` string. If the input is "ytmusic", it returns
        `wavelink.TrackSource.YouTubeMusic`. If the input is "soundcloud", it
        returns `wavelink.TrackSource.SoundCloud`. For any other input, it returns
        `wavelink.TrackSource.YouTube`.
    """
    async def getSource(self, source: str):
        match source:
            case "ytmusic":
                return wavelink.TrackSource.YouTubeMusic
            case "soundcloud":
                return wavelink.TrackSource.SoundCloud
            case _:
                return wavelink.TrackSource.YouTube

    """
    The `getTrack` function searches for a track or playlist based on the given search query and returns
    the track and an embed message.
    
    :param interaction: The parameter `interaction` is of type `discord.Interaction`, which represents the context of
    the interaction with the Discord API. It contains information about the user, the channel, and the
    server where the interaction occurred
    :type interaction: discord.Interaction
    :param search: The `search` parameter is a string that represents the query used to search for a
    track or playlist. It is used to search for either a specific song or a playlist on YouTube
    :type search: str
    :return: The function `getTrack` returns two values: `track` and `musicEmbed`.
    """
    async def getTrack(self, interaction: discord.Interaction, search: str, source : wavelink.enums.TrackSource):
        #*If a playlist is searched, search for the playlist, else search for the song
        tracks: wavelink.Search = await wavelink.Playable.search(search, source=source)
        if not tracks:
            await interaction.response.send_message(f'No tracks found with query: `{search}`')
            return

        if not isinstance(tracks, wavelink.Playlist):
            tracks: wavelink.Playable = tracks[0]
        return tracks
    
    async def createEmbed(self, track, embed_title):
        #*If a playlist is searched, the enbed will have a different format and it's title will be the playlist name, else the embed will have a different format and it's title will be the song title
        em = discord.Embed(title=f"{embed_title}", description=f"{track.title} by {track.author}", color=discord.Color.orange())
        #*These fields are only added if the track is not a playlist
        if track.artwork:
            em.set_thumbnail(url=track.artwork)
            em.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=track.length)) if not track.is_stream else "Live")
        return em
    

    """
    This function plays a track in a voice channel using a music player and handles playlist management.
    
    :param interaction: The `interaction` parameter is of type `discord.Interaction` and represents the context of the
    interaction, such as the user and the channel where the interaction occurred
    :type interaction: discord.Interaction
    :param vc: The parameter `vc` is of type `wavelink.Player`, which is a player object used for
    playing audio tracks in a voice channel
    :type vc: wavelink.Player
    :param track: The `track` parameter in the `playTrack` function is the track that you want to play.
    It can be either a single song or a playlist
    :param musicEmbed: The `musicEmbed` parameter is an embed object that contains information about the
    track that is being played. It is sent as a message in the Discord channel using the `send_message`
    method of the `interaction.response` object. The embed typically includes details such as the track title,
    artist, duration
    :return: nothing (None).
    """
    async def playTrack(self, interaction: discord.Interaction, vc: wavelink.Player, tracks):
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
        song_counter = 0
        songs = []
        em = discord.Embed(title="Queue (First 25 Songs added)", color=discord.Color.orange())
        #*Add the songs to the list and adds fields to the embed
        for song in vc.queue:
            if song_counter >= 25:
                break
            song_counter += 1
            songs.append(f"{song_counter}. {song}")
            em.add_field(name=f"{song_counter} - {song.title}", value=f"Duration: {str(datetime.timedelta(milliseconds=song.length))}", inline=False)
        return em
            
async def setup(bot):
    await bot.add_cog(Music(bot))