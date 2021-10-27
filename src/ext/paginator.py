import discord
from collections import OrderedDict
import asyncio
import pycord_components
from pycord_components import Button, ButtonStyle


class PaginatorSession:
    """Class that interactively paginates
    a set of embed using reactions."""

    def __init__(self, ctx, timeout=60, pages=None, color=discord.Color.green(), footer=''):
        if pages is None:
            pages = []
        self.footer = footer  # footer message
        self.ctx = ctx  # ctx
        self.timeout = timeout  # when the reactions get cleared, int[seconds]
        self.pages = pages  # the list of embeds list[discord.Embed, discord.Embed]
        self.running = False  # currently running, bool
        self.message = None  # current message being paginated, discord.Message
        self.current = 0  # current page index, int
        self.color = color  # embed color
        # can't be awaited here, must be done in PaginatorSession.run()

        self.reactions = OrderedDict({
            'â®': self.first_page,
            'â—€': self.previous_page,
            'â¹': self.close,
            'â–¶': self.next_page,
            'â­': self.last_page
        })

    # this wasn't used but i'll just leave it here i guess
    def add_page(self, page):
        if isinstance(page, discord.Embed):
            self.pages.append(page)
        else:
            raise TypeError('Page must be a discord.Embed.')

    def valid_page(self, index):
        return index >= 0 or index < len(self.pages)  # removed +1 so it's < instead of <=

    async def show_page(self, index: int):

        if not self.valid_page(index):
            return  # checks for a valid page

        self.current = index
        page = self.pages[index]  # gets the page
        page.set_footer(text=self.footer)  # sets footer

        if self.running:
            # if the first embed was sent, it edits it
            await self.message.edit(embed=page)
        else:
            self.running = True
            #view = ControlButtons()
            # sends the message
            components = [  # Use any button style you wish to :)
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

            self.message = await self.ctx.reply(embed=page, components=components)

    def react_check(self, reaction, user):
        """Check to make sure it only responds to reactions from the sender and on the same message."""
        if reaction.message.id != self.message.id:
            return False  # not the same message
        if user.id != self.ctx.author.id:
            return False  # not the same user
        if reaction.emoji in self.reactions.keys():
            return True  # reaction was one of the pagination emojis

    async def run(self):
        """Actually runs the paginator session."""
        if not self.running:
            # defaults to first page
            await self.show_page(0)
        while self.running:
            try:
                # waits for reaction using react_check
                reaction, user = await self.ctx.bot.wait_for('button_press',
                                                             check=self.react_check,
                                                             timeout=self.timeout)
                print(reaction, user)
            except asyncio.TimeoutError:
                self.running = False
                try:
                    await self.message.clear_reactions()  # tries to remove reactions
                except:
                    pass  # no perms
                finally:
                    break  # stops no matter what
            else:
                # same as above
                try:
                    await self.message.remove_reaction(reaction, user)
                except:
                    pass

                action = self.reactions[reaction.emoji]  # gets the function from the reaction map OrderedDict
                await action()  # awaits here with () because __init__ can't be async

    # all functions with await must be async
    async def first_page(self):
        """Go to the first page."""
        return await self.show_page(0)

    async def last_page(self):
        """Go to the last page."""
        return await self.show_page(len(self.pages) - 1)

    async def next_page(self):
        """Go to the next page."""
        if len(self.pages) - 1 < self.current + 1:
            return await self.show_page(self.current)
        else:
            return await self.show_page(self.current + 1)

    async def previous_page(self):
        """Go to the previous page."""
        if 0 == self.current:
            return await self.show_page(self.current)
        else:
            return await self.show_page(self.current - 1)

    async def close(self):
        """Stop the paginator session."""
        self.running = False
        try:
            await self.message.clear_reactions()
        except:
            pass

