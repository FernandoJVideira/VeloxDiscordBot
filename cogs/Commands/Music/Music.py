import os
import discord
import asyncio
import wavelink
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from cogs.UI import ButtonView
from cogs.Commands.Music.MusicUtils import MusicUtils
from cogs.constants import (
    NOT_PLAYING_MESSAGE, 
    UNKNOWN_ERROR_MESSAGE, 
    ROLE_REQUIRED_MESSAGE
)

class Music(commands.Cog):

    #*Constructor
    def __init__(self, bot):
        self.bot = bot
        self.musicUtils = MusicUtils(bot)
        
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
        embed: discord.Embed = await self.musicUtils.createEmbed(track, "Now Playing 🎵")
        await player.home.send(embed=embed, view=ButtonView(self),)

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
        #* Defer the bot's response
        await interaction.response.defer()

        #* Verify if the user is in a voice channel
        if not await self.musicUtils.checkVoiceChannel(interaction) or not await self.musicUtils.checkDJRole(interaction):
            return
        
        #* Get the source of the song based on the search query or the source parameter
        source = await self.musicUtils.checkURL(interaction, search) if source is None else await self.musicUtils.getSource(source)
        
        #* Verify if the bot is in a voice channel and connect if not
        vc = await self.musicUtils.connectToChannel(interaction)
        vc.autoplay = wavelink.AutoPlayMode.partial

        #* Lock the player to this channel...
        if not hasattr(vc, "home"):
            vc.home = interaction.channel
        elif vc.home != interaction.channel:
            await interaction.followup.send(f"You can only play songs in {vc.home.mention}, as the player has already started there.")
            return

        #* Get the track and create the embed
        track = await self.musicUtils.getTrack(interaction, search, source)
        await vc.queue.put_wait(track)

        #* Play the song
        await asyncio.sleep(1)  #* wait for 1 second for the vc.is_playing() to be updated
        if not vc.playing and not vc.paused:
            await interaction.followup.send(f"Now Playing {track.name if isinstance(track, wavelink.Playlist) else track.title}")
            await self.musicUtils.playTrack(interaction, vc, track)
        else:
            queue_embed = await self.musicUtils.createEmbed(track, "Added to queue 🎵")
            await interaction.followup.send(embed=queue_embed)
 
    async def pause(self, interaction: discord.Interaction):
        if not await self.musicUtils.checkVoiceChannel(interaction):
            return
        if not await self.musicUtils.checkDJRole(interaction):
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
        if not await self.musicUtils.checkDJRole(interaction):
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
        if not await self.musicUtils.checkVoiceChannel(interaction):
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
        if not await self.musicUtils.checkDJRole(interaction):
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
        if not await self.musicUtils.checkDJRole(interaction):
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
        if not await self.musicUtils.checkDJRole(interaction):
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

            
async def setup(bot):
    await bot.add_cog(Music(bot))