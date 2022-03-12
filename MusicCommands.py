import discord, youtube_dl, os
import asyncio
from discord.ext import commands

bot = commands.Bot(command_prefix = "!!")
queuelist = []
filestodelete = []

class musicBot(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    #@commands.has_role("DJ")
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        await channel.connect()
    
    @commands.command()
    #@commands.has_role("DJ")
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()
    
    @commands.command()
    #@commands.has_role("DJ")
    async def play(self, ctx, *, search):
        
        ydl_opts = {}
        voice = ctx.voice_client
        
        #Get the Title
        if search[0:4] == "http" or search[0:3] == "www":
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search, download = False)
                title = info["title"]
                url = search
        if search[0:4] != "http" or search[0:3] != "www":
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download = False)["entries"][0]
                title = info["title"]
                url = info["webpage_url"]
                
        ydl_opts = {
        'format' : 'bestaudio/best',
        "outtmpl" : f"{title}.mp3",
        "postprocessors": 
        [{"key" : "FFmpegExtractAudio", "preferredcodec" : "mp3", "preferredquality" : "192"}], 
        }
        def download(url):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, download, url)
        
        #Playing and Queueing Audio
        if voice.is_playing():
            queuelist.append(title)
            await ctx.send(f"Added to Queue: ** {title} **")
        else:
            voice.play(discord.FFmpegPCMAudio(f"{title}.mp3"), after = lambda e : check_queue())
            await ctx.send(f"Playing: ** {title} ** :musical_note:")
            filestodelete.append(title)
            await self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = title))
                        
        def check_queue():
            try:
                if queuelist[0] != None:
                    voice.play(discord.FFmpegPCMAudio(f"{queuelist[0]}.mp3"), after = lambda e : check_queue())
                    coro = self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = queuelist[0]))
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                    fut.result()
                    filestodelete.append(queuelist[0])
                    queuelist.pop(0)
            except IndexError:
                for file in filestodelete:
                    os.remove(f"{file}.mp3")  
                filestodelete.clear()
    
    @commands.command()
    #@commands.has_role("DJ")
    async def pause(self, ctx):
        voice = ctx.voice_client
        if voice.is_playing() == True:
            voice.pause()
        else:
            await ctx.send("Bot is not playing audio!")
    
    @commands.command()
    #@commands.has_role("DJ")
    async def skip(self, ctx):
        voice = ctx.voice_client
        if voice.is_playing() == True:
            voice.stop()
        else:
            await ctx.send("Bot is not playing audio!")
    
    @commands.command()
    #@commands.has_role("DJ")
    async def resume(self, ctx):
        voice = ctx.voice_client
        if voice.is_playing() == True:
            await ctx.send("Bot is playing audio!")
        else:
            voice.resume()
            
    @commands.command()
    async def viewqueue(self, ctx):
        await ctx.send(f"Queue: **{str(queuelist)} **")
    
    #Error Handlers
    @join.error
    async def errorhandler(self,ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("You have to be connected to a Voice Channel to use this command.")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("You have to have the DJ Role to use this bot.")
    
    @leave.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("Bot is not connected to a Voice Channel.")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("You have to have the DJ Role to use this bot.")
    
    #@play.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("Bot is not connected to a Voice Channel.")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("You have to have the DJ Role to use this bot.")
    
    @skip.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("Bot is not connected to a Voice Channel.")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("You have to have the DJ Role to use this bot.")
    
    @resume.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("Bot is not connected to a Voice Channel.")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("You have to have the DJ Role to use this bot.")
    
    @pause.error
    async def errorhandler(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send("Bot is not connected to a Voice Channel.")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("You have to have the DJ Role to use this bot.")
        
def setup(bot):
    bot.add_cog(musicBot(bot))