import compileall

import discord
import asyncio
from discord_components import DiscordComponents, Button, ButtonStyle, Interaction


class PaginatorSession:
    """Class that interactively paginates
    a set of embed using reactions."""

    def __init__(self, ctx, pages):
        if pages is None:
            pages = []
        self.ctx = ctx  # ctx
        self.pages = pages  # the list of embeds list[discord.Embed, discord.Embed]
        self.running = False  # currently running, bool
        self.message = None  # current message being paginated, discord.Message
        self.current = 0  # current page index, int
        self.dbot = DiscordComponents(self.ctx.bot)
        # can't be awaited here, must be done in PaginatorSession.run()

    def get_components(self):
        return [  # Use any button style you wish to :)
            [
                Button(
                    label="Prev",
                    id="back",
                    style=ButtonStyle.red
                ),
                Button(
                    label=f"Page {int(self.pages.index(self.pages[self.current])) + 1}/{len(self.pages)}",
                    id="cur",
                    style=ButtonStyle.grey,
                    disabled=True
                ),
                Button(
                    label="Next",
                    id="front",
                    style=ButtonStyle.red
                )
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
        self.message = await self.ctx.reply(
            "**Pagination!**",
            embed=self.pages[self.current],
            components=self.get_components()
        )
        # Infinite loop
        counter = 0
        while True:
            # Try and except blocks to catch timeout and break
            try:

                interaction = await self.ctx.bot.wait_for(
                    "button_click",
                    check=self.check_usage,  # You can add more
                    timeout=10.0  # 10 seconds of inactivity
                )
                # Getting the right list index
                if interaction.component.id == "back":
                    self.current -= 1
                elif interaction.component.id == "front":
                    self.current += 1
                # If its out of index, go back to start / end
                if self.current == len(self.pages):
                    self.current = 0
                elif self.current < 0:
                    self.current = len(self.pages) - 1

                # Edit to new page + the center counter changes
                await interaction.respond(
                    type=7,
                    embed=self.pages[self.current],
                    components=self.get_components()
                )
            except asyncio.TimeoutError:
                # Disable and get outta here
                await self.message.edit(
                    components=[
                        [
                            Button(
                                label="Prev",
                                id="back",
                                style=ButtonStyle.red,
                                disabled=True
                            ),
                            Button(
                                label=f"Page {int(self.pages.index(self.pages[self.current])) + 1}/{len(self.pages)}",
                                id="cur",
                                style=ButtonStyle.grey,
                                disabled=True
                            ),
                            Button(
                                label="Next",
                                id="front",
                                style=ButtonStyle.red,
                                disabled=True
                            )
                        ]
                    ]
                )
                break
