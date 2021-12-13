import discord


class ConfirmerSession:
    """Class that interactively paginates
    a set of embed using reactions."""

    def __init__(self, page, color=discord.Color.green(), footer=''):
        """Confirmer, for confirming things obv duh."""
        super().__init__()
        self.page = page  # the list of embeds list[discord.Embed, discord.Embed]

    async def run(self, message):
        """Asks the user a question to confirm something."""
        # We create the view and assign it to a variable so we can wait for it later.
        view = Confirm()
        message = await message.edit(embed=self.page, view=view)
        # Wait for the View to stop listening for input...
        await view.wait()
        message = await message.edit(embed=self.page, view=view)
        if view.value is None:
            return False, message
        elif view.value:
            return True, message
        else:
            return False, message


# Define a simple View that gives us a confirmation menu
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()
        self.remove_item(self.children[0])
        self.remove_item(self.children[0])

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()
        self.remove_item(self.children[0])
        self.remove_item(self.children[0])
