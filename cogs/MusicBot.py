import datetime
import os
import discord
import asyncio
import wavelink
from wavelink import TrackEventPayload
from discord.ext import commands
from discord import app_commands

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
        node: wavelink.Node = wavelink.Node(uri='lavalink:2333', password=os.getenv('LAVALINK_PASSWORD'), secure=False)
        #*Connect the node to the bot
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])
        
    #*Events
    @commands.Cog.listener()
    #*When the wavelink node is ready
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.id} is ready.")

    @commands.Cog.listener()
    #*When the track ends
    async def on_wavelink_track_end(self, payload: TrackEventPayload):
        #*Get the voice client
        vc = payload.player

        #*If the queue is empty and loop is disabled, wait for 30 secs before disconnecting
        if vc.queue.is_empty and not vc.queue.loop and not vc.is_playing():
            vc.auto_queue.clear()
            vc.autoplay = False
            await asyncio.sleep(30)
            await vc.disconnect()
            return
        
    #*Play command, plays a song in the voice channel
    @app_commands.command(name="play", description="Play a song in your voice channel.")
    @app_commands.describe(search="The song you want to play.")
    @app_commands.checks.has_role("DJ")
    async def play(self, ctx: discord.Interaction, search: str):
        
            #*Verify if the user is in a voice channel
            await self.checkVoiceChannel(ctx)
            
            #*Verify if the bot is in a voice channel and connect if not
            vc = await self.connectToChannel(ctx)
            
            #*Get the track and create the embed
            track, musicEmbed = await self.getTrack(ctx, search)

            #*Play the song
            await asyncio.sleep(1)  #* wait for 1 second for the vc.is_playing() to be updated
            if not vc.is_playing() and not vc.is_paused():
                await self.playTrack(ctx, vc, track, musicEmbed)
                return
            else:
                #*Add the song to the queue
                await vc.queue.put_wait(track)
                queueEmbed = await self.createEmbed(track, "Added to queue", ctx)
                await ctx.response.send_message(embed=queueEmbed)

 
    #*Pause command, pauses the current song
    @app_commands.command(name="pause", description="Pause the current song.")
    @app_commands.checks.has_role("DJ")
    async def pause(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return 
        #*Checks if the song is already paused
        elif vc.is_paused():
            await ctx.response.send_message("Already paused!")
            return
        #*If the song is playing, pause it
        await vc.pause()
        await ctx.response.send_message("Paused the current song.")

    #*Resume command, resumes the current song, if paused
    @app_commands.command(name="resume", description="Resumes the current song.")
    @app_commands.checks.has_role("DJ")
    async def resume(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if vc.is_playing():
            await ctx.response.send_message("Already playing!")
            return
        else:
            #*If the song is paused, resume it
            await vc.resume()
            await ctx.response.send_message("Resumed the current song.")

    #*Skip command, skips the current song
    @app_commands.command(name="skip", description="Skips the current song.")
    @app_commands.checks.has_role("DJ")
    async def skip(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return 

        #*If not playing, stop the player
        await vc.stop(force=True)
        #*If the queue is empty, disable autoplay, else skip the song and continue
        if vc.queue.is_empty:
            vc.autoplay = False
            await ctx.response.send_message("Skipped the current song. The queue is empty.")
        else:
            await ctx.response.send_message("Skipped the current song.")

    #*Queue command, shows the current queue
    @app_commands.command(name="queue", description="Shows the current queue.")
    async def queue(self, ctx: discord.Interaction):
        #*Gets the voice client and checks if it is playing
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.is_playing():
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
        if not vc.queue.is_empty:
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
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return
        #*Clears the queue
        vc.queue.clear()
        await ctx.response.send_message("Cleared the queue.")

    #*Disconnect command, disconnects the bot from the voice channel
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel.")
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
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return
        #*Loops the current song
        if vc.queue.loop:
            vc.queue.loop = False
            await ctx.response.send_message("Looping is now disabled.")
        else:
            vc.queue.loop = True
            await ctx.response.send_message("Looping is now enabled.")

    #*Error Handling, these functions are called when an error occurs sending a message to the user

    @play.error
    async def play_error(self, ctx: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        else:
            await ctx.response.send_message("Invalid search query.")
            print(error)

    @pause.error
    async def pause_error(self, ctx: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        else:
            await ctx.response.send_message("An unknown error occured.")

    @resume.error   
    async def resume_error(self, ctx: discord.Interaction, error):
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

    #*Checks if the user is in a voice channel
    async def checkVoiceChannel(self, ctx: discord.Interaction):
        #*Verify if the user is in a voice channel or in the same voice channel as the bot
        if not ctx.user.voice:
            await ctx.response.send_message("You must be in a voice channel to use this command.")
            return
        elif ctx.guild.voice_client and ctx.guild.voice_client.channel != ctx.user.voice.channel:
            await ctx.response.send_message("You must be in the same voice channel as the bot.")
            return
        
    async def connectToChannel(self, ctx: discord.Interaction):
        #*Verify if the bot is in a voice channel and connect if not
        if not ctx.guild.voice_client:
            vc: wavelink.Player = await ctx.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        else:
            vc: wavelink.Player = ctx.guild.voice_client
        return vc
    
    #*Gets the searched track and creates the embed
    async def getTrack(self, ctx: discord.Interaction, search: str):
        #*If a playlist is searched, search for the playlist, else search for the song
        if "playlist" in search:
            #*Search for the playlist
            track = await wavelink.YouTubePlaylist.search(search)
            if not track:
                await ctx.response.send_message(f'No tracks found with query: `{search}`')
                return
            musicEmbed = await self.createEmbed(track, "Now Playing", ctx, True)
        else:
            #*Search for the song
            track = await wavelink.YouTubeTrack.search(search)
            if not track:
                await ctx.response.send_message(f'No tracks found with query: `{search}`')
                return
            #*Get the first track from the list
            track = track[0]
            musicEmbed = await self.createEmbed(track,"Now Playing",ctx)
        return track, musicEmbed

    #*Creates an embed for the searched track/playlist
    async def createEmbed(self, track, embedTitle, ctx, playlist=False):
        #*If a playlist is searched, the enbed will have a different format and it's title will be the playlist name, else the embed will have a different format and it's title will be the song title
        em = discord.Embed(title=f"{embedTitle}", description=f"{track.name if playlist else track.title}", color=discord.Color.orange())
        #*These fields are only added if the track is not a playlist
        if not playlist:
            thumbURL = await track.fetch_thumbnail()
            em.set_thumbnail(url=thumbURL)
            em.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=track.duration)))
        em.add_field(name="Requested by", value=ctx.user.mention)
        return em
    
    #*Plays the track
    async def playTrack(self, ctx: discord.Interaction, vc: wavelink.Player, track, musicEmbed):
        #*Send the embed created in getTrack()
        await ctx.response.send_message(embed=musicEmbed)
        #*Set the autoplay to True in case theres Queue management involved (for example, if a user plays more than a song or a playlist)
        vc.autoplay = True
        #*If the track is a playlist, play the first song and add the rest to the queue
        if isinstance(track, wavelink.YouTubePlaylist):
            await vc.play(track.tracks[0])
            for song in track.tracks[1:]:
                await vc.queue.put_wait(song)
        else:
            #*If the track is a song, play it
            await vc.play(track)
            return
    
    #*Gets the queue embed
    async def getQueueEmbed(self, vc: wavelink.Player):
        #*Set a counter and a list of songs
        songCounter = 0
        songs = []
        #*Get the queue and create the embed
        queue = vc.queue.copy()
        em = discord.Embed(title="Queue", color=discord.Color.orange())

        #*Add the songs to the list and adds fields to the embed
        for song in queue:
            songCounter += 1
            songs.append(f"{songCounter}. {song.title}")
            em.add_field(name=f"{songCounter} - {song.title}", value=f"Duration: {str(datetime.timedelta(milliseconds=song.duration))}", inline=False)
        return em
            
async def setup(bot):
    await bot.add_cog(Music(bot))