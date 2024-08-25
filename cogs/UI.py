import discord

class ButtonUI(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, custom_id: str, music_cog):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.music_cog = music_cog

    async def callback(self, interaction: discord.Interaction):
        if self.custom_id == "pause_button":
            await self.music_cog.pause(interaction)
        elif self.custom_id == "skip_button":
            await self.music_cog.skip(interaction)
        elif self.custom_id == "stop_button":
            await self.music_cog.disconnect(interaction)
        elif self.custom_id == "loop_button":
            await self.music_cog.loop(interaction)
        elif self.custom_id == "queueloop_button":
            await self.music_cog.queueLoop(interaction)
        # Add more button interactions as needed

class ButtonView(discord.ui.View):
    def __init__(self, music_cog):
        super().__init__()
        self.add_item(ButtonUI(label="⏯️", style=discord.ButtonStyle.secondary, custom_id="pause_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="⏭️", style=discord.ButtonStyle.success, custom_id="skip_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="⏹️", style=discord.ButtonStyle.danger, custom_id="stop_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="🔁", style=discord.ButtonStyle.primary, custom_id="loop_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="🔂", style=discord.ButtonStyle.secondary, custom_id="queueloop_button", music_cog=music_cog))