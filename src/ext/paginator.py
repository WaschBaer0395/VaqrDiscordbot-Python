import compileall

import discord
from discord import abc
from discord.interactions import Interaction
from discord.utils import MISSING
from discord.commands import ApplicationContext
from discord.ext.commands import Context


class PaginatorSession(discord.ui.View):
    """Class that interactively paginates
    a set of embed using reactions."""

    def __init__(self, pages):
        """Paginator, for paginating pages duh."""
        if pages is None:
            pages = []
        super().__init__(timeout=10)
        self.pages = pages  # the list of embeds list[discord.Embed, discord.Embed]
        self.page_count = len(self.pages)
        self.running = False  # currently running, bool
        self.message = None  # current message being paginated, discord.Message
        self.current = 0  # current page index, int
        self.user = None
        self.previous_button = self.children[0]
        self.page_counter = self.children[1]
        self.forward_button = self.children[2]
        # can't be awaited here, must be done in PaginatorSession.run()

    async def interaction_check(self, interaction: Interaction) -> bool:
        return self.user == interaction.user

    def change_label(self, current):
        self.children[1].label = "Page " + str(current+1) + "/" + str(self.page_count)

    async def on_timeout(self) -> None:
        self.remove_item(self.children[0])
        self.remove_item(self.children[0])
        self.remove_item(self.children[0])
        await self.edit_message()

    async def edit_message(self):
        self.message = await self.message.edit(
            content=self.page if isinstance(self.page, str) else None,
            embed=self.page if isinstance(self.page, discord.Embed) else MISSING,
            view=self,
        )

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.red, disabled=False)
    async def prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current == 0:
            self.current = self.page_count - 1
        else:
            self.current -= 1

        page = self.pages[self.current]
        self.change_label(self.current)
        await interaction.response.edit_message(
            content=page if isinstance(page, str) else None,
            embed=page if isinstance(page, discord.Embed) else MISSING,
            view=self,
        )

    @discord.ui.button(label="Page", style=discord.ButtonStyle.grey, disabled=True)
    async def page(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.red, disabled=False)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current == self.page_count:
            self.current = 0
        else:
            self.current += 1

        page = self.pages[self.current]
        self.change_label(self.current)
        await interaction.response.edit_message(
            content=page if isinstance(page, str) else None,
            embed=page if isinstance(page, discord.Embed) else MISSING,
            view=self,
        )

    async def run(self, messageable: abc.Messageable, ephemeral: bool = False):
        if not isinstance(messageable, abc.Messageable):
            raise TypeError("messageable should be a subclass of abc.Messageable")

        page = self.pages[0]
        self.change_label(0)
        if isinstance(messageable, (ApplicationContext, Context)):
            self.user = messageable.author

        if isinstance(messageable, ApplicationContext):
            self.message = await messageable.respond(
                content=page if isinstance(page, str) else None,
                embed=page if isinstance(page, discord.Embed) else MISSING,
                view=self,
            )
        else:
            self.message = await messageable.send(
                content=page if isinstance(page, str) else None,
                embed=page if isinstance(page, discord.Embed) else MISSING,
                view=self,
            )
        return self.message

    def next_button(self, label: str, color: str = "primary"):
        self.forward_button.label = label
        color = getattr(discord.ButtonStyle, color.lower())
        self.forward_button.style = color

    def back_button(self, label: str, color: str = "primary"):
        self.previous_button.label = label
        color = getattr(discord.ButtonStyle, color.lower())
        self.previous_button.style = color
