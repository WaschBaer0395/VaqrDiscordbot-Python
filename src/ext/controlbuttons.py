import discord


class ControlButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="◄◄", style=discord.ButtonStyle.secondary)
    async def first(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("First", ephemeral=True)
        self.value = 'first'
        self.stop()

    @discord.ui.button(label="◄", style=discord.ButtonStyle.secondary)
    async def prev(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("Prev", ephemeral=True)
        self.value = 'prev'
        self.stop()

    @discord.ui.button(label="█", style=discord.ButtonStyle.secondary)
    async def end(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("Stop", ephemeral=True)
        self.value = 'end'
        self.stop()

    @discord.ui.button(label="►", style=discord.ButtonStyle.secondary)
    async def next(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("Next", ephemeral=True)
        self.value = 'next'
        self.stop()

    @discord.ui.button(label="►►", style=discord.ButtonStyle.secondary)
    async def last(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("Last", ephemeral=True)
        self.value = 'last'
        self.stop()
