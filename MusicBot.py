import nextcord
import wavelink
from nextcord.ext import commands, application_checks
from nextcord import Interaction, SlashOption

bot = commands.Bot(command_prefix = ".ds ", help_command = None, intents = nextcord.Intents().all())

class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.node_connect())

    async def node_connect(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot = self.bot, host="lava.link", port=80, password="dismusic")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node <{node.identifier}> is ready!")
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        ctx = player.ctx
        vc = ctx.guild.voice_client

        if vc.loop:
            return await player.play(track)
        
        
        next_song = vc.queue.get()
        await player.play(next_song)
        await ctx.send(f"Now playing: `{next_song.title}`")

    @bot.slash_command(name="play", description="Play a song in your voice channel.")
    async def play(self, ctx : Interaction, search: str = SlashOption(description="The song you want to play.")):
        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client # define our voice client

        if not vc: # check if the bot is not in a voice channel
            vc = await ctx.user.voice.channel.connect(cls=wavelink.Player) # connect to the voice channel

        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message

        song = await wavelink.YouTubeTrack.search(query=search, return_first=True) # search for the song

        if not song: # check if the song is not found
            return await ctx.send("No song found.") # return an error message

        if vc.queue.is_empty and not vc.is_playing(): # check if the queue is empty
            await vc.play(song) # play the song
            await ctx.send(f"Now playing: `{vc.source.title}`") # return a message
        
        else:
            await vc.queue.put_wait(song) # add the song to the queue
            await ctx.send(f"Added `{song.title}` to the queue.") # return a message
        vc.ctx = ctx
        setattr(vc, "loop", False) # set the loop to False


    @bot.slash_command(name="pause", description="Pause the current song.")
    async def pause(self, ctx : Interaction):

        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")
        
        if application_checks.has_role("DJ") == False:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client

        if not vc: # check if the bot is not in a voice channel
            return await ctx.send("You are not playing any music...") # return an error message
        
        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message
        
        await vc.pause() # pause the song
        await ctx.send("Paused ya music ;)") # return a message

    @bot.slash_command(name="resume", description="Resume the current song.")
    async def resume(self, ctx : Interaction):

        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")

        if application_checks.has_role("DJ") == False:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client

        if not vc: # check if the bot is not in a voice channel
            return await ctx.send("You are not playing any music...") # return an error message
        
        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message
        
        await vc.resume() # pause the song
        await ctx.send("Ayeee the music's backkk!!") # return a message

    
    @bot.slash_command(name="stop", description="Stops current song.")
    async def stop(self, ctx : Interaction):

        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")

        if application_checks.has_role("DJ") == False:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client

        if not vc: # check if the bot is not in a voice channel
            return await ctx.send("You are not playing any music...") # return an error message
        
        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message
        
        await vc.stop() # pause the song
        await ctx.send("Stopped ur song :(") # return a message

    @bot.slash_command(name="disconnect", description="Disconnects the bot")
    async def disconnect(self, ctx : Interaction):

        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")

        if application_checks.has_role("DJ") == False:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client

        if not vc: # check if the bot is not in a voice channel
            return await ctx.send("You are not playing any music...") # return an error message
        
        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message
        
        await vc.disconnect() # pause the song
        await ctx.send("Hasta la vista babyyyyy!") # return a message
    
    @bot.slash_command(name="loop", description="Pause the current song.")
    async def loop(self, ctx : Interaction):

        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")
        
        if application_checks.has_role("DJ") == False:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client

        if not vc: # check if the bot is not in a voice channel
            return await ctx.send("You are not playing any music...") # return an error message
        
        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message
        
        try:
            vc.loop ^= True
        except Exception:
            setattr(vc, "loop", False)
        
        if vc.loop:
            return await ctx.send("Looping the current song.")
        else:
            return await ctx.send("Unlooped the current song.")

    @bot.slash_command(name="queue", description="Shows the queue")
    async def queue(self, ctx : Interaction):

        role = nextcord.utils.get(ctx.guild.roles, name="DJ")

        if role not in ctx.user.roles:
            return await ctx.send("You don't have the permission to use this command.")
        
        if application_checks.has_role("DJ") == False:
            return await ctx.send("You don't have the permission to use this command.")

        vc = ctx.guild.voice_client

        if not vc: # check if the bot is not in a voice channel
            return await ctx.send("You are not playing any music...") # return an error message
        
        if ctx.user.voice.channel.id != vc.channel.id: # check if the bot is not in the voice channel
            return await ctx.send("You must be in the same voice channel as the bot.") # return an error message

        if vc.queue.is_empty:
            return await ctx.send("The queue is empty.")
        
        em = nextcord.Embed(title="Queue", description="The current queue.", color=nextcord.Color.blurple())
        queue = vc.queue.copy()
        song_count = 0
        for song in queue:
            song_count += 1
            em.add_field(name=f"Song {song_count}", value=f"**Title:** {song.title}\n**Duration:** {song.duration}", inline=False)

        return await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Music(bot))
    


    