import compileall

import discord
from discord import Component, Button, Interaction
from discord.ext import commands
from discord import ButtonStyle
from discord.types.components import ButtonComponent
import asyncio


class PaginatorSession(commands.Cog):
    """Class that interactively paginates
    a set of embed using reactions."""

    def __init__(self, ctx, pages):
        if pages is None:
            pages = []
        self.ctx = ctx  # ctx
        self.ctx.add_view(view=discord.ui.View(timeout=None))
        self.pages = pages  # the list of embeds list[discord.Embed, discord.Embed]
        self.running = False  # currently running, bool
        self.message = None  # current message being paginated, discord.Message
        self.current = 0  # current page index, int
        self.interaction = None
        # can't be awaited here, must be done in PaginatorSession.run()

    @commands.Cog.listener()
    async def on_ready(self):
        """This function is called every time the bot restarts.
        If a view was already created before (with the same custom IDs for buttons)
        it will be loaded and the bot will start watching for button clicks again.
        """

        # we recreate the view as we did in the /post command
        view = discord.ui.View(timeout=None)
        # make sure to set the guild ID here to whatever server you want the buttons in

        # add the view to the bot so it will watch for button interactions
        self.ctx.add_view(view)

    def get_components(self):
        return [  # Use any button style you wish to :)
            [
                Button(data=ButtonComponent(style=ButtonStyle.red, type=2)),
                Button(data=ButtonComponent(style=ButtonStyle.red, type=2)),
                Button(data=ButtonComponent(style=ButtonStyle.red, type=2))
            ]
        ]

    def check_usage(self, interaction):
        if interaction.component.id not in ["front", "back"]:
            return False
        if self.ctx.author.id != interaction.author.id:
            return False
        if self.message.id != interaction.message.id:
            return False
        return True

    async def run(self):
        # Sets a default embed
        self.current = 0
        # Sending first message
        # I used ctx.reply, you can use simply send as well
        self.message = await self.ctx.send(
            "**Pagination!**",
            embed=self.pages[self.current],
            components=self.get_components()
        )
        # Infinite loop
        counter = 0
        while True:
            # Try and except blocks to catch timeout and break
            try:

                self.interaction = await self.ctx.bot.wait_for(
                    "button_click",
                    check=self.check_usage,  # You can add more
                    #timeout=10.0  # 10 seconds of inactivity
                )
                # Getting the right list index
                if self.interaction.component.id == "back":
                    self.current -= 1
                elif self.interaction.component.id == "front":
                    self.current += 1
                # If its out of index, go back to start / end
                if self.current == len(self.pages):
                    self.current = 0
                elif self.current < 0:
                    self.current = len(self.pages) - 1

                # Edit to new page + the center counter changes
                await self.interaction.edit_origin(
                    embed=self.pages[self.current],
                    components=self.get_components()
                )
            except asyncio.TimeoutError:
                # Disable and get outta here
                await self.message.edit(
                    components=[
                        [
                            Button(data=ButtonComponent(style=ButtonStyle.red, type=2)),
                            Button(data=ButtonComponent(style=ButtonStyle.red, type=2)),
                            Button(data=ButtonComponent(style=ButtonStyle.red, type=2))
                        ]
                    ]
                )
                break
