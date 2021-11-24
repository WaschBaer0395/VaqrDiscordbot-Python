import compileall

import discord
from discord import Component, Button, Interaction, Message


class PaginatorSession(discord.ui.View):
    """Class that interactively paginates
    a set of embed using reactions."""

    def __init__(self, ctx, pages):
        super().__init__(timeout=None)
        if pages is None:
            pages = []
        self.ctx = ctx  # ctx
        self.pages = pages  # the list of embeds list[discord.Embed, discord.Embed]
        self.message = None  # current message being paginated, discord.Message
        self.current = 0  # current page index, int
        self.view = None
        # can't be awaited here, must be done in PaginatorSession.run()

    def check_usage(self, interaction):
        if self.ctx.author.id != interaction.user.id:
            return False
        if self.message.id != interaction.message.id:
            return False
        return True

    async def update_message(self, message, current):
        view = Buttons(
            pages=self.pages,
            current=current,
            ctx=self.ctx,
            message=message)
        #editing the center button to show the current page
        child_1 = view.children[1]
        child_1.label = "Page " + str(self.current) + "/" + str(len(self.pages))
        view.children[1] = child_1
        #editing the message
        self.message = await Message.edit(message,
                                          embed=self.pages[self.current],
                                          view=view)

    async def next_page(self, message):
        if self.current != len(self.pages) - 1:
            self.current += 1
        else:
            self.current = 0
        await self.update_message(message, self.current)

    async def prev_page(self, message):
        if self.current != 0:
            self.current -= 1
        else:
            self.current = len(self.pages) - 1
        await self.update_message(message, self.current)

    async def run(self):
        self.current = 0
        self.message = await self.ctx.reply(embed=self.pages[self.current])
        await self.update_message(self.message, self.current)


class Buttons(PaginatorSession):
    def __init__(self, pages, ctx, current, message):
        super().__init__(ctx=ctx, pages=pages)
        self.pages = pages
        self.current = current
        self.message = message

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.blurple, custom_id="prev")
    async def prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        if super().check_usage(interaction):
            await super().prev_page(self.message)

    @discord.ui.button(style=discord.ButtonStyle.gray,
                       custom_id="page",
                       label="Page",
                       disabled=False)
    async def on_ready(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.stop()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="next")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if super().check_usage(interaction):
            await super().next_page(self.message)
