import datetime
import os
import discord
import asyncio
import wavelink
from wavelink import TrackEventPayload
from discord.ext import commands
from discord import app_commands

class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.setup_hook())

    async def setup_hook(self):
        await self.bot.wait_until_ready()
        node: wavelink.Node = wavelink.Node(
            #uri='lavalink:2333', password=os.getenv('LAVALINK_PASSWORD'), secure=False)
            uri='https://lavalink-server.03pleaser-minst.repl.co:443', password='youshallnotpass', secure=True)
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])
        
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.id} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: TrackEventPayload):
        vc = payload.player

        if vc.queue.is_empty and not vc.queue.loop:
            vc.auto_queue.clear()
            vc.autoplay = False
            asyncio.sleep(30)
            vc.disconnect()
            return
        
        
    @app_commands.command(name="play", description="Play a song in your voice channel.")
    @app_commands.describe(search="The song you want to play.")
    @app_commands.checks.has_role("DJ")
    async def play(self, ctx: discord.Interaction, search: str):
        
            #Verify if the user is in a voice channel
            if not ctx.user.voice:
                await ctx.response.send_message("You must be in a voice channel to use this command.")
                return
            elif ctx.guild.voice_client and ctx.guild.voice_client.channel != ctx.user.voice.channel:
                await ctx.response.send_message("You must be in the same voice channel as the bot.")
                return
            
            #Verify if the bot is in a voice channel and connect if not
            elif not ctx.guild.voice_client:
                vc: wavelink.Player = await ctx.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
            else:
                vc: wavelink.Player = ctx.guild.voice_client

            if "playlist" in search:
                track = await wavelink.YouTubePlaylist.search(search)
                if not track:
                    await ctx.response.send_message(f'No tracks found with query: `{search}`')
                    return
                musicEmbed = discord.Embed(title="Now Playing", description=f"{track.name}", color=discord.Color.orange())
                musicEmbed.add_field(name="Requested by", value=ctx.user.mention)

            elif "soundcloud.com" in search:
                track = await wavelink.SoundCloudTrack.search(search)
                if not track:
                    await ctx.response.send_message(f'No tracks found with query: `{search}`')
                    return
                musicEmbed = discord.Embed(title="Now Playing", description=f"{track.title}", color=discord.Color.orange())
                thumbURL = await track.fetch_thumbnail()
                musicEmbed.set_thumbnail(url=thumbURL)
                musicEmbed.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=track.duration)))
                musicEmbed.add_field(name="Requested by", value=ctx.user.mention)
            else:
                #Search for the song
                track = await wavelink.YouTubeTrack.search(search)
                if not track:
                    await ctx.response.send_message(f'No tracks found with query: `{search}`')
                    return
                track = track[0]
                musicEmbed = discord.Embed(title="Now Playing", description=f"{track.title}", color=discord.Color.orange())
                thumbURL = await track.fetch_thumbnail()
                musicEmbed.set_thumbnail(url=thumbURL)
                musicEmbed.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=track.duration)))
                musicEmbed.add_field(name="Requested by", value=ctx.user.mention)

            #Play the song
            if not vc.is_playing() or not vc.is_paused():
                await ctx.response.send_message(embed=musicEmbed)
                vc.autoplay = True
                if isinstance(track, wavelink.YouTubePlaylist):
                    first_song = track.tracks[0]
                    await vc.play(first_song, populate=False)
                    for song in track.tracks[1:]:
                        await vc.queue.put_wait(song)
                else:
                    await vc.play(track, populate=False)
                    return
            else:
                await vc.queue.put_wait(track)
                queueEmbed = discord.Embed(title="Added to queue", description=f"{track.title}", color=discord.Color.orange())
                thumbURL = await track.fetch_thumbnail()
                queueEmbed.set_thumbnail(url=thumbURL)
                queueEmbed.add_field(name="Duration", value=str(datetime.timedelta(milliseconds=track.duration)))
                queueEmbed.add_field(name="Requested by", value=ctx.user.mention)
                await ctx.response.send_message(embed=queueEmbed)

 
    @app_commands.command(name="pause", description="Pause the current song.")
    @app_commands.checks.has_role("DJ")
    async def pause(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return

        await vc.pause()
        await ctx.response.send_message("Paused the current song.")

    @app_commands.command(name="resume", description="Resumes the current song.")
    @app_commands.checks.has_role("DJ")
    async def resume(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client
        if vc.is_playing():
            await ctx.response.send_message("Already playing!")
            return
        else:
            await vc.resume()
            await ctx.response.send_message("Resumed the current song.")

    @app_commands.command(name="skip", description="Skips the current song.")
    @app_commands.checks.has_role("DJ")
    async def skip(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client
        
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return

        await vc.stop(force=True)
        if vc.queue.is_empty:
            vc.autoplay = False
            await ctx.response.send_message("Skipped the current song. The queue is empty.")
        else:
            await ctx.response.send_message("Skipped the current song.")

    @app_commands.command(name="queue", description="Shows the current queue.")
    async def queue(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client

        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return
        #Verify if the user is in a voice channel
        elif not ctx.user.voice:
            await ctx.response.send_message("You must be in a voice channel to use this command.")
            return
        elif ctx.guild.voice_client and ctx.guild.voice_client.channel != ctx.user.voice.channel:
            await ctx.response.send_message("You must be in the same voice channel as the bot.")
            return
        
        if not vc.queue.is_empty:
            songCounter = 0
            songs = []
            queue = vc.queue.copy()
            embed = discord.Embed(title="Queue", color=discord.Color.orange())

            for song in queue:
                songCounter += 1
                songs.append(f"{songCounter}. {song.title}")
                embed.add_field(name=f"{songCounter} - {song.title}", value=f"Duration: {str(datetime.timedelta(milliseconds=song.duration))}", inline=False)

            await ctx.response.send_message(embed=embed)
        else:
            await ctx.response.send_message("The queue is empty.")
    
    @app_commands.command(name="clear", description="Clears the current queue.")
    @app_commands.checks.has_role("DJ")
    async def clear(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return

        vc.queue.clear()
        await ctx.response.send_message("Cleared the queue.")


    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel.")
    @app_commands.checks.has_role("DJ")
    async def disconnect(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc:
            await ctx.response.send_message("I am not connected to a voice channel.")
            return

        await vc.disconnect()
        await ctx.response.send_message("Disconnected from the voice channel.")
    
    @app_commands.command(name="loop", description="Loops the current song.")
    @app_commands.checks.has_role("DJ")
    async def loop(self, ctx: discord.Interaction):
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            await ctx.response.send_message("I am not playing anything.")
            return

        if vc.queue.loop:
            vc.queue.loop = False
            await ctx.response.send_message("Looping is now disabled.")
        else:
            vc.queue.loop = True
            await ctx.response.send_message("Looping is now enabled.")

    #Error Handling

    @play.error
    async def play_error(self, ctx: discord.Interaction, error):

        if isinstance(error, app_commands.errors.MissingRole):
            await ctx.response.send_message("You must have the DJ role to use this command.")
        #elif isinstance(error, wavelink.Track):
        else:
            await ctx.response.send_message("An unknown error occured.")
            print(error.args)

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
            
async def setup(bot):
    await bot.add_cog(Music(bot))