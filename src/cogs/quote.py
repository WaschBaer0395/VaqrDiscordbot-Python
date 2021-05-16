import re
from distutils.util import strtobool

import discord
from discord.ext import commands

from ext.SQLlite import SqlLite
from ext.config import check_config, save_config
from ext.confirmer import ConfirmerSession


class Quotes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = SqlLite('Quotes')
        self.init_db()
        self.settings = {
            'channelSet': 'False',
            'Name': 'None',
            'ID': 'None',
        }

    def init_db(self):
        statement = ''' CREATE TABLE IF NOT EXISTS Quotes( \
                        Quote text NOT NULL,\
                        UserName text NOT NULL, \
                        UserID text, \
                        ByUser text NOT NULL, \
                        Date text NOT NULL\
                        );'''
        self.db.create_table(statement)

    @commands.command(aliases=['q_set', 'q_init', 'qinit', 'qset'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def setup_quotes(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        '''Admin Only!!, setup Quotes channel'''
        if len(channel) > 1:
            await ctx.send(embed=discord.Embed(description=f"Quotes can only be saved in 1 channel. Please try again.",
                                               colour=discord.Colour(0xbf212f)))

            return
        elif len(channel) <= 0:
            await ctx.send(embed=discord.Embed(description=f"Please enter a channel",
                                               colour=discord.Colour(0xbf212f)))

            return
        else:
            embedctx = None
            config, self.settings = check_config('QUOTES', self.settings)
            try:
                if bool(strtobool(config.get('QUOTES', 'channelSet'))):
                    embedctx, config = await channel_set(ctx, config, channel, reassign=True)
                else:
                    embedctx, config = await channel_set(ctx, config, channel, reassign=False)
                save_config(config)
            except Exception as e:
                await ctx.send('```' + str(e) + '```')
                #raise e
                return

            embed = discord.Embed(description=f"The Quotes channel was set to <#{channel[0].id}>"
                                              f" with an id of {channel[0].id}", colour=discord.Colour(0x37b326))
            msg = await self.introduction(ctx, channel[0])
            await embedctx.edit(embed=embed)

    async def introduction(self, ctx, channel):
        message = f'Hello, my name is {self.bot.user.name} , and i am the Quote-Master.\n' \
                  f'In this channel you will find all the quotes\n' \
                  f'that people on this discord have added.\n' \
                  f'You can get a random quote from this list,\n' \
                  f'by typing either ``!quote`` or ``!quote random`` \n' \
                  f'**in any channel that supports commands except for this one!** \n' \
                  f'If you want a specific quote, you can do for example: ``!quote 69`` , \n' \
                  f'LOL 69 HAHA!! \n' \
                  f'Have fun and be polite! Don\'t add quotes to bully someone!\n' \
                  f'**Admins can remove quotes!** \n'
        embed = discord.Embed(description=message, colour=discord.Colour(0x37b326))
        msg = await channel.send(embed=embed)
        await msg.pin()
        return

    @commands.command(aliases=['quote_del'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def del_quote(self, ctx):
        print('del quote')

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def quote_add_admin(self, ctx, *, arg):
        message = arg
        print(message)

    @commands.command()
    async def quote(self, ctx):
        message = ctx.message
        message_content = message.content
        message_author = message.author

        message_content = message_content.replace('v!quote', '', 1)
        if message_content.startswith(' '):
            message_content = message_content.replace(' ', '', 1)
        print('Original Message -> ' + message_content)

        if message_content.startswith('random') or len(message_content) == 0:
            print('Random Quote -> Random')
        elif message_content.isnumeric():
            print('Sending Quote NR. {}'.format(message_content))
        elif message_content.startswith('add '):
            message_content = message_content.replace('add ', '', 1)
            if re.match(r"(.+[\s][-][\s].+)", message_content):
                print('Quote detected!')
                quote, about = message_content.split(' - ')
                if re.match(r"^<@![0-9]+>$", about):
                    print('Detected Tagged User')
                else:
                    print('No User was Tagged')
            print('Quote -> ' + message_content)

            #(.+[\s][-][\s].+) for checking String - String
            #^<![0-9]+>$ for checking <!numbers>
        else:
            print('Wrong Syntax')

    async def add_quote(self, content, author):
        print('Quote: {} added by: {}'.format(content, author.id))


async def channel_set(ctx, config, channel, reassign):
    if reassign:
        embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78)
                              , description="Are you sure you want the Bot to post the Quotes in the selected channel ?")
        c_session = ConfirmerSession(ctx, page=embed)
        response, embedctx = await c_session.run()
    else:
        embed = discord.Embed(title="Setting New Channel", colour=discord.Colour(0x269a78)
                              , description="Setting channel")
        embedctx = await ctx.send(embed=embed)
        response = True
    if response is True:
        config = configset(config, channel[0])
    else:
        embed = discord.Embed(description=f"The Quotes channel was not set",
                              colour=discord.Colour(0xbf212f))
        await embedctx.edit(embed=embed)
        return embedctx, config
    return embedctx, config


def configset(config, channel):
    config.set('QUOTES', 'channelSet', str(True))
    config.set('QUOTES', 'Name', str(channel.name))
    config.set('QUOTES', 'ID', str(channel.id))
    return config


def setup(bot):
    bot.add_cog(Quotes(bot))
