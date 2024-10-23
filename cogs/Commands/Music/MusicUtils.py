import datetime
import discord
from discord.utils import get
import wavelink

class MusicUtils:
    def __init__(self, bot):
        self.bot = bot

    async def connectToChannel(self, interaction: discord.Interaction):
        #*Verify if the bot is in a voice channel and connect if not
        if not interaction.guild.voice_client:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        else:
            vc: wavelink.Player = interaction.guild.voice_client
        return vc
    

    async def checkURL(self, search: str):
        #*Check if the search query is a URL
        if search.startswith("https://youtu"):
            return wavelink.TrackSource.YouTube
        elif search.startswith("https://soundcloud"):
            return wavelink.TrackSource.SoundCloud
        elif search.startswith("https://music.youtube"):
            return wavelink.TrackSource.YouTubeMusic
        else:
            return wavelink.TrackSource.YouTube
        

    async def checkDJRole(self, interaction: discord.Interaction):
        #*Check if the user has the DJ role
        dj_role = get(interaction.guild.roles, name="DJ")
        if dj_role not in interaction.user.roles:
            await interaction.response.send_message("You must have the DJ role to use this command.", ephemeral=True, delete_after=5)
            return False
        return True
    
    async def checkVoiceChannel(self, interaction: discord.Interaction):
        #* Verify if the user is in a voice channel
        if interaction.user.voice is None:
            await interaction.response.send_message(
                "You must be in a voice channel to use this command.",
                ephemeral=True,
                delete_after=5
            )
            return False
        elif interaction.guild.voice_client and interaction.guild.voice_client.channel != interaction.user.voice.channel:
            await interaction.response.send_message(
                "You must be in the same voice channel as the bot.",
                ephemeral=True,
                delete_after=5
            )
            return False
        return True


    async def getSource(self, source: str):
        match source:
            case "ytmusic":
                return wavelink.TrackSource.YouTubeMusic
            case "soundcloud":
                return wavelink.TrackSource.SoundCloud
            case _:
                return wavelink.TrackSource.YouTube

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
    

    async def playTrack(self, vc: wavelink.Player, tracks):
        #*Play the track from the queue
        await vc.play(tracks)
    

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
