import discord
from collections import OrderedDict
import asyncio


class ConfirmerSession:
    '''Class that interactively paginates
    a set of embed using reactions'''

    def __init__(self, ctx, timeout=60, page='', color=discord.Color.green(), footer=''):
        self.footer = footer  # footer message
        self.ctx = ctx  # ctx
        self.timeout = timeout  # when the reactions get cleared, int[seconds]
        self.page = page  # the list of embeds list[discord.Embed, discord.Embed]
        self.running = False  # currently running, bool
        self.message = None  # current message being paginated, discord.Message
        self.current = 0  # current page index, int
        self.color = color  # embed color
        # can't be awaited here, must be done in PaginatorSession.run()
        self.reactions = OrderedDict({
            '✅': self.accept,
            '❌': self.deny
        })

    async def show_page(self):

        page = self.page  # gets the page
        page.set_footer(text=self.footer)  # sets footer

        if self.running:
            # if the first embed was sent, it edits it
            await self.message.edit(embed=page)
        else:
            self.running = True
            # sends the message
            self.message = await self.ctx.send(embed=page)

            # adds reactions
            for reaction in self.reactions.keys():
                await self.message.add_reaction(reaction)

    def react_check(self, reaction, user):
        '''Check to make sure it only responds to reactions from the sender and on the same message'''
        if reaction.message.id != self.message.id:
            return False  # not the same message
        if user.id != self.ctx.author.id:
            return False  # not the same user
        if reaction.emoji in self.reactions.keys():
            return True  # reaction was one of the confirmer emojis

    async def run(self):
        '''Actually runs the confirmer session'''
        if not self.running:
            # display the embed
            await self.show_page()
        while self.running:
            try:
                # waits for reaction using react_check
                reaction, user = await self.ctx.bot.wait_for('reaction_add', check=self.react_check, timeout=self.timeout)
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
                response = await action()  # awaits here with () because __init__ can't be async
                return response, self.message

    # all functions with await must be async
    async def accept(self):
        '''Accept the prompt'''

        try:
            await self.message.clear_reactions()
        except:
            pass

        self.running = False
        return True

    async def deny(self):
        '''Deny the prompt'''

        try:
            await self.message.clear_reactions()
        except:
            pass

        self.running = False
        return False
