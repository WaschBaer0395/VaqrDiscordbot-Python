import math

import discord
import configparser
from discord.ext import commands
from distutils.util import strtobool
from ext.SQLlite import SqlLite

from ext.confirmer import ConfirmerSession

channelSet = False
channelName = None
channelID = None
currentCount = None

bot = commands.Bot('')


class WrongCount(Exception):
    pass


class Counting(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = SqlLite('Counting')
        self.init_db()

    def init_db(self):
        statement = ' \
                    CREATE TABLE IF NOT EXISTS COUNTING( \
                        UserID integer PRIMARY KEY, \
                        UserName text NOT NULL, \
                        Discriminator text NOT NULL, \
                        Nickname text, \
                        Counts Integer, \
                        MissCounts integer, \
                        Experience integer, \
                        Level integer \
                    );'
        self.db.create_table(statement)

    @commands.command(aliases=['setcounting', 'setcount', 'setupcounting', 'countingchannel', 'sc'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def set_counting(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        '''Admin Only!!, setup counting channel'''
        if len(channel) > 1:
            await ctx.send(discord.Embed(description=f"Counting can only be applied in 1 channel. Please try again.",
                                         colour=discord.Colour(0xbf212f)))

            return
        else:
            embedctx = None
            config = check_config()
            try:
                if bool(strtobool(config.get('COUNTING', 'channelSet'))):

                    embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78)
                                          , description="Are you sure you want to restart counting in a new channel?")
                    c_session = ConfirmerSession(ctx, page=embed)
                    response, embedctx = await c_session.run()
                    if response is True:
                        config = configset(config, channel[0])
                    else:
                        embed = discord.Embed(description=f"The counting channel was not set",
                                              colour=discord.Colour(0xbf212f))
                        await embedctx.edit(embed=embed)
                        return
                else:
                    config = configset(config, channel[0])
                save_config(config)
            except Exception as e:
                await ctx.send('```' + str(e) + '```')
                return

            embed = discord.Embed(description=f"The counting channel was set to <#{channel[0].id}>"
                                              f" with an id of {channel[0].id}", colour=discord.Colour(0x37b326))
            await embedctx.edit(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            config = check_config()
            if int(config.get('COUNTING', 'id')) != int(message.channel.id):
                return
            else:
                if message.content.isnumeric():
                    if int(config.get('COUNTING', 'currentCount')) + 1 == int(message.content):
                        guild = self.bot.get_guild(message.guild.id)
                        channel = guild.get_channel(message.channel.id)

                        if int(message.content) % 1000 == 420:
                            msg = str(message.content)[:-3]
                            embed = discord.Embed(description=f"" + msg + "**420** BlazeIt :potted_plant:",
                                                  colour=discord.Colour(0x21afbf))
                            await channel.send(embed=embed)
                        elif int(message.content) % 100 == 69:
                            msg = str(message.content)[:-2]
                            embed = discord.Embed(description=f"" + msg + "**69** LUL :point_right: :ok_hand:",
                                                  colour=discord.Colour(0x21afbf))
                            await channel.send(embed=embed)

                        config.set('COUNTING', 'currentCount', message.content)
                        save_config(config)
                        if not self.check_id(message.author.id):
                            self.reg_user(message.author)
                        else:
                            self.add_count(message.author.id)
                    else:
                        raise WrongCount
                else:
                    raise WrongCount
        except WrongCount:
            if not message.author.id == self.bot.user.id:
                await message.delete()
                self.wrong_count(message.author.id)

            return

    def check_id(self, userid):
        statement = '''SELECT EXISTS(SELECT 1 FROM Counting WHERE UserID=?)'''
        count = self.db.execute_statement(statement, (userid,))
        print(count[1][0][0])
        if count[1][0][0] >= 1:
            return True
        else:
            return False

    def reg_user(self, author):
        statement = '''INSERT INTO Counting (UserID,UserName,Discriminator,Nickname,Counts,MissCounts,Experience,Level)
                    VALUES(?,?,?,?,?,0,0,1)'''
        args = (int(author.id), str(author.display_name), int(author.discriminator), str(author.nick), 1)
        self.db.execute_statement(statement, args)

    def add_count(self, authorid):
        statement = '''SELECT * FROM Counting WHERE UserID = ?'''
        args = (str(authorid),)
        ret = self.db.execute_statement(statement, args)[1][0]
        count = ret[4]
        curr_exp = ret[6]
        curr_level = ret[7]
        statement = '''UPDATE Counting SET Counts=?'''
        args = (str(count + 1),)
        self.db.execute_statement(statement, args)
        self.add_xp(curr_exp, curr_level)

    def add_xp(self, curr_exp, curr_level):
        newexp = curr_exp + 10
        newlevel = calc_lvl(newexp)
        statement = '''UPDATE Counting Set Experience=?, Level=?'''
        args = (str(newexp), str(newlevel),)
        self.db.execute_statement(statement, args)

    def wrong_count(self, authorid):
        statement = '''SELECT * FROM Counting WHERE UserID = ?'''
        args = (str(authorid),)
        ret = self.db.execute_statement(statement, args)[1][0][5]
        statement = '''UPDATE Counting SET MissCounts=? WHERE UserID=?'''
        args = (str(ret + 1), str(authorid))
        self.db.execute_statement(statement, args)


def check_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # checking for existing config
    if config.has_section('COUNTING'):
        channelName = config.get('COUNTING', 'Name')
        channelID = config.get('COUNTING', 'ID')
        currentCount = config.get('COUNTING', 'currentCount')
        channelSet = config.get('COUNTING', 'channelSet')
    else:
        # writing default config, incase none has been found
        config['COUNTING'] = \
            {
                'channelSet': 'False',
                'Name': 'None',
                'ID': 'None',
                'currentCount': '0',
            }
        try:
            with open('settings.ini', 'a+') as configfile:
                config.write(configfile)
        except Exception as e:
            print('```error writing config: ' + str(e) + ' ```')
    return config


def configset(config, channel):
    config.set('COUNTING', 'channelSet', str(True))
    config.set('COUNTING', 'Name', str(channel.name))
    config.set('COUNTING', 'ID', str(channel.id))
    config.set('COUNTING', 'currentCount', str(0))
    return config


def save_config(config):
    with open('settings.ini', 'w+') as configfile:
        config.write(configfile)
        return True


def calc_lvl(curr_exp):
    ''''
    calculates the resulting level, from given exp points
    :param curr_exp: current experience
    :return: resulting level truncated eg. 4.6 = 4
    '''
    lvl = math.trunc(math.floor(25 + math.sqrt(625 + 100 * curr_exp)) / 50)
    return int(lvl)


def calc_exp(curr_level):
    exp = 25 * curr_level * curr_level - 25 * curr_level
    return int(exp)


def setup(bot):
    bot.add_cog(Counting(bot))
