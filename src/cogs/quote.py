import random
import re
import discord

from distutils.util import strtobool
from discord.ext import commands
from ext.SQLlite import SqlLite
from ext.config import check_config, save_config
from ext.confirmer import ConfirmerSession
from datetime import datetime
from pytz import timezone


class Quotes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = SqlLite('Quotes')
        self.init_db()
        self.conf = None
        self.settings = {
            'channelSet': 'False',
            'Name': 'None',
            'ID': 'None',
        }
        self.pride = [
            '0xe40303',     # red
            '0xff8c00',     # orange
            '0xffed00',     # yellow
            '0x008026',     # green
            '0x004dff',     # blue
            '0x750787',     # purple
            '0xFFFFFE',     # white
            '0xF7A8B8',     # pink
            '0x55CDFC',     # lightblue
            '0x453326',     # brown
            '0x000001'      # black
        ]
        self.init_config()

    def init_db(self):
        statement = ''' CREATE TABLE IF NOT EXISTS Quotes( \
                        Quote text NOT NULL,\
                        AboutName text NOT NULL, \
                        AboutID text DEFAULT ('0'), \
                        ByUser text NOT NULL, \
                        Date text NOT NULL,\
                        MessageID text DEFAULT ('0'),\
                        MessageColor text DEFAULT ('0xbf212f')\
                        );'''
        self.db.create_table(statement)

    def init_config(self):
        self.conf, self.settings = check_config('BIRTHDAY', self.settings)

    @commands.command(aliases=['q_set', 'q_init', 'qinit', 'qset'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def setup_quotes(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """Admin Only!!, setup Quotes channel"""
        if len(channel) > 1:
            await ctx.send(embed=discord.Embed(description=f"Quotes can only be saved in 1 channel. Please try again.",
                                               colour=discord.Colour(0xbf212f)))

            return
        elif len(channel) <= 0:
            await ctx.send(embed=discord.Embed(description=f"Please enter a channel",
                                               colour=discord.Colour(0xbf212f)))

            return
        else:
            config, self.settings = check_config('QUOTES', self.settings)
            try:
                if bool(strtobool(config.get('QUOTES', 'channelSet'))):
                    embedctx, config = await channel_set(ctx, config, channel, reassign=True)
                else:
                    embedctx, config = await channel_set(ctx, config, channel, reassign=False)
                save_config(config)
            except Exception as e:
                await ctx.send(
                    embed=discord.Embed(description=f"{e}", colour=discord.Colour(0xbf212f)))
                raise e

            embed = discord.Embed(description=f"The Quotes channel was set to <#{channel[0].id}>"
                                              f" with an id of {channel[0].id}", colour=discord.Colour(0x37b326))
            await self.introduction(channel[0])
            await embedctx.edit(embed=embed)

    async def introduction(self, channel):
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
        print(ctx)

    @commands.command()
    async def quote(self, ctx):
        message = ctx.message
        message_content = message.content
        message_author = message.author
        about_id = 0

        message_content = message_content.replace('v!quote', '', 1)
        if message_content.startswith(' '):
            message_content = message_content.replace(' ', '', 1)
        try:
            if message_content.startswith('random') or len(message_content) == 0:
                quote = await self.get_quote()
                ctx = await self.show_quote(ctx, quote)
            elif message_content.isnumeric():
                quote = await self.get_quote(nr=message_content)
                ctx = await self.show_quote(ctx, quote)
            elif message_content.startswith('add '):
                message_content = message_content.replace('add ', '', 1)
                if re.match(r"(.+[\s][-][\s].+)", message_content):     # (.+[\s][-][\s].+) for checking String - String
                    quote, about = message_content.split(' - ')
                    if re.match(r"^<@![0-9]+>$", about):                # ^<@![0-9]+>$ for checking <!numbers>
                        about_id = int(about.replace('<@!', '').replace('>', ''))
                        about_name = self.bot.get_user(about_id).name
                    else:
                        about_name = about

                    quote_nr = await self.add_quote_to_db(about_id, about_name, message_author, quote)
                    await self.post_quote(quote_nr)

                else:
                    await ctx.send(
                        embed=discord.Embed(
                            description=f"The Quote you entered, has the wrong format Please try again.\n"
                                        f"the needed format is \n"
                                        f"`v!quote add \"Quote\" - Name` or\n"
                                        f"`v!quote add \"Quote\" - @person`",
                            colour=discord.Colour(0xbf212f)))
            else:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"Wrong Syntax\n"
                                    f"You can use the following commands \n"
                                    f"`v!quote random` or `v!quote` to get a random quote\n"
                                    f"`v!quote <nr>` to get a specific quote\n"
                                    f"`v!quote add <quote> - <name or @person>` to add a quote",
                        colour=discord.Colour(0xbf212f)))
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(description=f"{e}", colour=discord.Colour(0xbf212f)))
            raise e

    async def get_quote(self, nr='random'):
        if nr == 'random':
            n_of_quotes = int(self.db.execute_statement('''SELECT COUNT(*) FROM Quotes''')[1][0][0])
            nr = random.randint(1, n_of_quotes)
        statement = '''SELECT ROWID, * FROM Quotes WHERE ROWID=?'''
        args = (nr,)
        quote = self.db.execute_statement(statement, args)[1][0]
        return quote

    async def add_quote_to_db(self, about_id, about_name, message_author, quote):
        curr_date = timezone('UTC').localize(datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
        statement = '''INSERT INTO Quotes (Quote,AboutName,AboutID,ByUser,Date) VALUES(?,?,?,?,?)'''
        if not quote.startswith('\"'):
            quote = '\"' + quote
        if not quote.endswith('\"'):
            quote = quote + '\"'
        args = (quote, about_name, about_id, message_author.id, curr_date, )
        self.db.execute_statement(statement, args)
        statement = '''SELECT last_insert_rowid()'''
        quote_id = self.db.execute_statement(statement)[1][0][0]
        return quote_id

    async def post_quote(self, quote_nr):
        # random_number = random.randint(0, 16777215)
        # hex_number = str(hex(random_number))
        # color = '0x' + hex_number[2:]
        c_index = (quote_nr-1) % 11

        statement = '''SELECT ROWID, * FROM Quotes WHERE rowid = ?'''
        args = (quote_nr,)
        quote = self.db.execute_statement(statement, args)[1][0]

        embed = await self.generate_quote_embed(quote, self.pride[c_index])
        quotes_channel = self.bot.get_channel(int(self.conf.get('QUOTES', 'ID')))
        await quotes_channel.send(embed=embed)

        statement = '''UPDATE Quotes SET MessageID=?, MessageColor=? WHERE rowid = ?'''
        args = (quotes_channel.last_message_id, str(self.pride[c_index]), quote[0],)
        self.db.execute_statement(statement, args)

    async def generate_quote_embed(self, quote, color=None):
        if quote[3] == '0':
            user = quote[2]
        else:
            user = '<@!' + quote[3] + '>'
        message_author = self.bot.get_user(int(quote[4]))
        if color is None:
            color = quote[7]
        embed = discord.Embed(description=f"{quote[1]} - {user}\n", colour=discord.Colour(int(color, 16)))
        embed.set_author(name=f"#{quote[0]} by {message_author}", icon_url=message_author.avatar.url)
        embed.timestamp = datetime.strptime(quote[5], '%Y-%m-%d %H:%M')
        return embed

    async def show_quote(self, ctx, quote):
        embed = await self.generate_quote_embed(quote, quote[7])
        await ctx.send(embed=embed)
        return ctx


async def channel_set(ctx, config, channel, reassign):
    if reassign:
        embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78),
                              description="Are you sure you want the Bot to post the Quotes in the selected channel ?")
        c_session = ConfirmerSession(ctx, page=embed)
        response, embedctx = await c_session.run()
    else:
        embed = discord.Embed(title="Setting New Channel", colour=discord.Colour(0x269a78),
                              description="Setting channel")
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
