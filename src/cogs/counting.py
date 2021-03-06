import math

import discord
from discord.ext import commands
from distutils.util import strtobool
from ext.db import DB
from ext.config import *

from ext.confirmer import ConfirmerSession

channelSet = False
channelName = None
channelID = None
currentCount = None

bot = commands.Bot('')


class WrongCount(Exception):
    pass


class Counting(commands.Cog):

    def __init__(self, _bot):
        """Cog for counting from 1 to infinity in a selected channel."""
        self.bot = _bot
        self.db = DB('Counting')
        self.init_db()
        self.settings = {
            'channelSet': 'False',
            'Name': 'None',
            'ID': 'None',
            'currentCount': '0',
        }

    def init_db(self):
        statement = ' \
                    CREATE TABLE IF NOT EXISTS COUNTING( \
                        UserID integer PRIMARY KEY, \
                        UserName VARCHAR(255) NOT NULL, \
                        Discriminator VARCHAR(255) NOT NULL, \
                        Nickname VARCHAR(255), \
                        Counts Integer, \
                        MissCounts integer, \
                        Experience integer, \
                        Level integer \
                    );'
        self.db.create_table(statement)

    @commands.command(aliases=['setcounting', 'setcount', 'setupcounting', 'countingchannel', 'sc'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def set_counting(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """Admin Only!!, setup counting channel."""
        if len(channel) > 1:
            await ctx.send(embed=discord.Embed(
                description=f"Counting can only be applied in 1 channel. Please try again.",
                colour=discord.Colour(0xbf212f)))

            return
        elif len(channel) <= 0:
            await ctx.send(embed=discord.Embed(description=f"Please enter a channel!.",
                                               colour=discord.Colour(0xbf212f)))

            return
        else:
            config, self.settings = check_config('COUNTING', self.settings)
            try:
                if bool(strtobool(config.get('COUNTING', 'channelSet'))):
                    message, config = await channel_set(ctx, config, channel, reassign=True)
                else:
                    message, config = await channel_set(ctx, config, channel, reassign=False)
                save_config(config)
            except Exception as e:
                raise e

            embed = discord.Embed(description=f"The counting channel was set to <#{channel[0].id}>"
                                              f" with an id of {channel[0].id}", colour=discord.Colour(0x37b326))
            await message.edit(embed=embed)

    @commands.command(aliases=['c'])
    async def count(self, ctx, args='help'):
        config, self.settings = check_config('COUNTING', self.settings)
        if int(config.get('COUNTING', 'id')) != ctx.channel.id:
            if args == 'help' or None:
                embed = discord.Embed(title="Counting usage",
                                      description="`v!c argument` \n"
                                                  "or\n"
                                                  "`v!count argument`\n"
                                                  "\n"
                                                  "**Arguments:** \n"
                                                  "\n"
                                                  "`list`\n`top10`\n`leaderboard` \n"
                                                  "for showing the leaderboard \n"
                                                  "\n"
                                                  "**Example:**  `v!c leaderboard`",
                                      colour=discord.Colour(0x37b326))
                await ctx.send(embed=embed)
            elif args == 'leaderboard' or args == 'top10' or args == 'list':
                await self.get_top10(ctx)
            elif args == 'rank':
                await self.show_rank(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            config, self.settings = check_config('COUNTING', self.settings)
            if config.get('COUNTING', 'id') != str(message.channel.id):
                return
            else:
                if message.content.isnumeric():
                    if int(config.get('COUNTING', 'currentCount')) + 1 == int(message.content):
                        guild = self.bot.get_guild(message.guild.id)
                        channel = guild.get_channel(message.channel.id)
                        xp_bonus = 1
                        if int(message.content) % 1000 == 420:
                            msg = str(message.content)[:-3]
                            embed = discord.Embed(description=f"" + msg + "**420** BlazeIt :potted_plant:",
                                                  colour=discord.Colour(0x21afbf))
                            await channel.send(embed=embed)
                            xp_bonus = 3
                        elif int(message.content) % 100 == 69:
                            msg = str(message.content)[:-2]
                            embed = discord.Embed(description=f"" + msg + "**69** LUL :six::nine:",
                                                  colour=discord.Colour(0x21afbf))
                            await channel.send(embed=embed)
                            xp_bonus = 3

                        config.set('COUNTING', 'currentCount', message.content)
                        save_config(config)
                        if not self.check_id(message.author.id):
                            self.reg_user(message.author)
                        else:
                            newlvl, lvlup, = self.add_count(message.author.id, xp_bonus)
                            if lvlup:
                                await channel.send('<@' + str(message.author.id) +
                                                   '> Congrats to the Lvl up, you reached LVL: ' +
                                                   str(newlvl) + ' in counting')
                    else:
                        raise WrongCount
                else:
                    raise WrongCount
        except WrongCount:
            if not self.check_bot(message):
                await message.delete()
                self.wrong_count(message.author.id)

            return

    async def show_rank(self, ctx):
        statement = ''' SELECT UserID,UserName,Counts,MissCounts,Level,Experience
                        FROM Counting 
                        WHERE UserID=%s'''
        args = (ctx.author.id,)
        ret = self.db.execute_statement(statement, args)[1][0]

        description = f"<@{ret[0]}> `Lvl: {ret[4]}` ,   " \
                      f"Counts: `{ret[2]}` ,   " \
                      f"Misscounts: `{ret[3]}` ,   " \
                      f"XP: `{ret[5]} / {calc_exp(int(ret[4]) + 1)}`"

        embed = discord.Embed(
            title='Rank for: ' + ret[1],
            description=description,
            colour=discord.Colour(0x37b326))
        await ctx.send(embed=embed)

    def check_id(self, userid):
        statement = '''SELECT EXISTS(SELECT 1 FROM Counting WHERE UserID=%s)'''
        count = self.db.execute_statement(statement, (userid,))
        if count[1][0][0] >= 1:
            return True
        else:
            return False

    def reg_user(self, author):
        statement = '''INSERT INTO Counting (UserID,UserName,Discriminator,Nickname,Counts,MissCounts,Experience,Level)
                    VALUES(%s,%s,%s,%s,%s,'0','0','1')'''
        args = (int(author.id), str(author.display_name), int(author.discriminator), str(author.nick), 1)
        self.db.execute_statement(statement, args)

    def add_count(self, authorid, xp_bonus):
        statement = '''SELECT * FROM Counting WHERE UserID = %s'''
        args = (str(authorid),)
        ret = self.db.execute_statement(statement, args)[1][0]
        count = ret[4]
        curr_exp = ret[6]
        statement = '''UPDATE Counting SET Counts=%s WHERE UserID=%s'''
        args = (str(count + 1), str(authorid),)
        self.db.execute_statement(statement, args)
        return self.add_xp(curr_exp, authorid, xp_bonus)

    def add_xp(self, curr_exp, authorid, xp_bonus):
        newexp = curr_exp + 10 * xp_bonus
        oldlevel = calc_lvl(curr_exp)
        newlevel = calc_lvl(newexp)
        statement = '''UPDATE Counting Set Experience=%s, Level=%s WHERE UserID=%s'''
        args = (str(newexp), str(newlevel), str(authorid),)
        self.db.execute_statement(statement, args)
        if newlevel != oldlevel:
            return newlevel, True
        return oldlevel, False

    def wrong_count(self, authorid):
        if not self.check_id(authorid):
            return
        statement = '''SELECT * FROM Counting WHERE UserID = %s'''
        args = (str(authorid),)
        ret = self.db.execute_statement(statement, args)
        statement = '''UPDATE Counting SET MissCounts=%s WHERE UserID=%s'''
        args = (str(ret[1][0][5] + 1), str(authorid))
        self.db.execute_statement(statement, args)

    def check_bot(self, message):
        if message.author.id == self.bot.user.id:
            return True
        else:
            return False

    async def get_top10(self, ctx):
        statement = '''
                    SELECT UserID,UserName,Counts,MissCounts,Level,Experience
                    FROM Counting 
                    ORDER BY Counts DESC LIMIT 10'''
        ret = self.db.execute_statement(statement)[1]
        description = ''
        c = 1
        for r in ret:
            n_lvl_xp = calc_exp(r[4] + 1)
            description = description + f"`#{c}` `lvl {str(r[4])}` <@{str(r[0])}> " \
                                        f"- `{str(r[2])}` counts " \
                                        f"- `{str(r[3])}` miscounts " \
                                        f"- `{str(r[5])} / {n_lvl_xp}xp` \n"
            c = c + 1

        embed = discord.Embed(
            title='TOP 10 Counters',
            description=description,
            colour=discord.Colour(0x37b326))
        await ctx.send(embed=embed)


async def channel_set(ctx, config, channel, reassign):
    if reassign:
        embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78),
                              description="Are you sure you want to restart counting in a new channel?")
        c_session = ConfirmerSession(page=embed)
        message = await ctx.send(embed=embed)
        response, message = await c_session.run(message)
    else:
        embed = discord.Embed(title="Setting New Channel", colour=discord.Colour(0x269a78),
                              description="Setting channel")
        message = await ctx.send(embed=embed)
        response = True
    if response is True:
        config = configset(config, channel[0])
    else:
        embed = discord.Embed(description="The counting channel was not set",
                              colour=discord.Colour(0xbf212f))
        await message.edit(embed=embed)
        return message, config
    return message, config


def configset(config, channel):
    config.set('COUNTING', 'channelSet', str(True))
    config.set('COUNTING', 'Name', str(channel.name))
    config.set('COUNTING', 'ID', str(channel.id))
    config.set('COUNTING', 'currentCount', str(0))
    return config


def calc_lvl(curr_exp):
    """'
    calculates the resulting level, from given exp points
    :param curr_exp: current experience
    :return: resulting level truncated eg. 4.6 = 4
    """
    lvl = math.trunc(math.floor(25 + math.sqrt(625 + 100 * curr_exp)) / 50)
    return int(lvl)


def calc_exp(curr_level):
    exp = 25 * curr_level * curr_level - 25 * curr_level
    return int(exp)


def setup(_bot):
    bot.add_cog(Counting(_bot))
