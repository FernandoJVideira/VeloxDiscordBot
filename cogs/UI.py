import discord

class ButtonUI(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, custom_id: str, music_cog):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.music_cog = music_cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.controller_id:
            await interaction.response.send_message("You are not authorized to use these controls.", ephemeral=True)
            return
        match self.custom_id:
            case "pause_button":
                await self.music_cog.pause(interaction)
            case "skip_button":
                await self.music_cog.skip(interaction)
            case "stop_button":
                await self.music_cog.disconnect(interaction)
            case "loop_button":
                await self.music_cog.loop(interaction)
            case "queueloop_button":
                await self.music_cog.queueLoop(interaction)
            case "seek_back":
                await self.music_cog.seek(interaction, -10000)
            case "seek_ahead":
                await self.music_cog.seek(interaction, 10000) 
            case _:
                pass

class ButtonView(discord.ui.View):
    def __init__(self, music_cog, controller_id):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.controller_id = controller_id

        self.add_item(ButtonUI(label="⏪", style=discord.ButtonStyle.secondary, custom_id="seek_back", music_cog=music_cog))
        self.add_item(ButtonUI(label="⏯️", style=discord.ButtonStyle.primary, custom_id="pause_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="⏩", style=discord.ButtonStyle.secondary, custom_id="seek_ahead", music_cog=music_cog))
        self.add_item(ButtonUI(label="⏭️", style=discord.ButtonStyle.success, custom_id="skip_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="⏹️", style=discord.ButtonStyle.danger, custom_id="stop_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="🔁", style=discord.ButtonStyle.primary, custom_id="loop_button", music_cog=music_cog))
        self.add_item(ButtonUI(label="🔂", style=discord.ButtonStyle.secondary, custom_id="queueloop_button", music_cog=music_cog))