import asyncio
import re
import threading
import discord

from discord.ext import commands, tasks
from discord.utils import get

from ext.SQLlite import SqlLite
from ext.config import *
from ext.confirmer import ConfirmerSession
from datetime import datetime
from pytz import timezone

bot = commands.Bot('')


class Birthday(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.conf = None
        self.settings = None
        self.db = SqlLite('Birthdays')
        self.init_db()
        self.init_config()

    @commands.Cog.listener()
    async def on_ready(self):
        print('BirthdayBot Ready')
        self.del_obs_members()
        found, birthday_kids = self.find_birthday(datetime.now())
        if found:
            await self.greet_birthday_kids(birthday_kids)
        # self.check_time()

    def init_config(self):
        settings = {
                'channelSet': 'False',
                'Init-ChannelName': 'None',
                'Init-ChannelID': 'None',
                'Announcetime': '8:00am',
                'Announcetimezone': 'US/Pacific',
                'Announce-ChannelID': 'None',
                'Announce-ChannelName': 'None',
                'SingularMessage': 'Has their Birthday today, wish them a happy birthday!',
                'PluralMessage': 'Have their Birthday today, wish them a happy birthday!'
        }
        self.conf, self.settings = check_config('BIRTHDAY', settings)

    def init_db(self):
        statement = ' \
                           CREATE TABLE IF NOT EXISTS Birthday( \
                               UserID integer PRIMARY KEY, \
                               UserName text NOT NULL, \
                               Discriminator text NOT NULL, \
                               Nickname text, \
                               MonthDayDisp text, \
                               Month integer, \
                               Day integer, \
                               Timezone text ' \
                    ');'
        self.db.create_table(statement)

    @commands.command()
    async def bset(self, ctx, *, args=None):
        '''<birthday> Setup your Birthday by entering the date'''
        day, month, err = get_date_month(args)
        config, self.settings = check_config('BIRTHDAY', self.settings)
        if err:
            await ctx.send(embed=discord.Embed(description=f'Unrecognized date format. \n'
                                                           f'The following formats are accepted, as examples: \n'
                                                           f'`15-jan`, `jan-15`, `15 jan`,\n'
                                                           f'`jan 15`, `15 January`, `January 15`',
                                               colour=discord.Colour(0xbf212f)))
            return
        else:
            monthday = find_month(month)[0][:3] + '-' + day
            self.add_birthday(ctx.author, monthday, find_month(month)[1], day)
            await ctx.send(embed=discord.Embed(description=f"Your Birthday was set for: `{day}-{find_month(month)[0]}`\n"
                                                           f"Birthdays will always be announced at"
                                                           f" {self.config.get('BIRTHDAY', 'Announcetime')}"
                                                           f" {self.config.get('BIRTHDAY', 'Announcetimezone')}",
                                               colour=discord.Colour(0x37b326)))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def bforcedel(self, ctx, member: commands.Greedy[discord.Member]):
        '''<user> Force Delete a birthday'''
        self.del_birthday(member[0].id)
        await ctx.send(embed=discord.Embed(description=f"Birthday for : <@{member[0].id}>, was deleted",
                                           colour=discord.Colour(0x37b326)))
        return

    @commands.command()
    async def bdel(self, ctx):
        '''Delete your birthday from the DB'''
        self.del_birthday(ctx.author.id)
        await ctx.send(embed=discord.Embed(description=f"Your Birthday was deleted",
                                           colour=discord.Colour(0x37b326)))
        return

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def binit(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        '''<commandChannel> <announceChannel> Setup Birthday Channel'''
        if len(channel) != 2:
            await ctx.send(embed=discord.Embed(description=f"Syntax is `bset <birthdaychannel> <Accouncementchannel>`\n"
                                                           f"you have either selected only 1, or more than 2 channels",
                                               colour=discord.Colour(0xbf212f)))
            return
        else:
            try:
                embedctx = await self.channel_set(ctx, channel[0], channel[1])
                save_config(self.config)
            except Exception as e:
                await ctx.send('```' + str(e) + '```')
                return
            embed = discord.Embed(description=f"The Birthday-Command Channel was set to: \n"
                                              f"<#{channel[0].id}> -`{channel[0].id}`"
                                              f"\n"
                                              f"The Birthday-Announce Channel was set to: \n"
                                              f"<#{channel[1].id}> -`{channel[1].id}`", colour=discord.Colour(0x37b326))
            await embedctx.edit(embed=embed)

    def check_time(self):
        # This function runs periodically every Hour
        threading.Timer(600, self.check_time).start()
        utc = timezone('UTC')
        utc_now = utc.localize(datetime.utcnow())
        user_time = utc_now
        if utc_now != datetime.now():
            user_tz = timezone(self.config.get('BIRTHDAY', 'Announcetimezone'))
            user_time = user_time.astimezone(user_tz).strftime("%H:%M")

        in_time = datetime.strptime(self.config.get('BIRTHDAY', 'Announcetime'), "%I:%M%p")
        out_time = datetime.strftime(in_time, "%H:%M")

        print('current check Time: {} vs. {}'.format(user_time, out_time))

        if user_time == out_time:
            print('Happy birthday')
            #await asyncio.sleep(300)

    async def greet_birthday_kids(self, birthday_kids):
        names = ''
        count = 1
        number_kids = len(birthday_kids)
        for b in birthday_kids:
            names = names + '<@{}>'.format(b.id)
            if count != number_kids-1:
                names = names + ' , '
            if count == number_kids-1:
                names = names + ' and '
            count = count + 1

        channel = discord.utils.get(self.bot.guilds[0].channels, id=int(self.conf.get('BIRTHDAY', 'Announce-ChannelID')))
        if len(birthday_kids) > 1:
            await channel.send(names + self.conf.get('BIRTHDAY', 'PluralMessage') + ' @here')
        else:
            await channel.send(names + self.conf.get('BIRTHDAY', 'SingularMessage') + ' @here')

    def del_obs_members(self):
        statement = '''SELECT UserID FROM Birthday'''
        ret, data = self.db.execute_statement(statement)
        member_ids = []
        bday_ids = []
        for d in data:
            bday_ids.append(d[0])
        for m in self.bot.guilds[0].members:
            member_ids.append(m.id)

        non_match = non_match_elements(bday_ids, member_ids)
        if len(non_match) != 0:
            for id in non_match:
                self.del_birthday(id)

    def find_birthday(self, curr_date):
        statement = '''SELECT UserID FROM Birthday WHERE Day=? AND month=?'''
        args = (curr_date.day, curr_date.month)
        ret, data = self.db.execute_statement(statement, args)
        temp = []
        birthday_kids = []
        for d in data:
            temp.append(d[0])
        for m in self.bot.guilds[0].members:
            if m.id in temp:
                birthday_kids.append(m)
        if len(birthday_kids) == 0:
            return False, None
        else:
            return True, birthday_kids

    def update_birthday(self, user, md, m, d):
        statement = ''' UPDATE Birthday SET MonthDayDisp=?,Month=?,Day=? WHERE UserID=?'''
        args = (md, m, d, user.id,)
        ret, err = self.db.execute_statement(statement, args)
        print(err)
        return ret

    def add_birthday(self, user, md, m, d):
        statement = ''' INSERT INTO Birthday (UserID,UserName,Discriminator,Nickname,MonthDayDisp,Month,Day,Timezone)  
                        VALUES(?,?,?,?,?,?,?,'')'''

        args = (str(user.id), user.name, user.discriminator, user.nick, md, str(m), str(d),)
        ret, err = self.db.execute_statement(statement, args)
        if 'UNIQUE' in str(err):
            ret = self.update_birthday(user, md, m, d)
        return ret

    def del_birthday(self, userid):
        statement = ''' DELETE FROM Birthday WHERE UserID=?'''
        args = (str(userid),)
        ret, data = self.db.execute_statement(statement, args)
        return ret

    async def channel_set(self, ctx, channel, a_channel):
        embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78)
                              , description="Are you sure you want to Set the BirthdayChannel ?")
        b_session = ConfirmerSession(ctx, page=embed)
        response, embedctx = await b_session.run()
        if response is True:
            self.config.set('BIRTHDAY', 'Init-ChannelName', str(channel.name))
            self.config.set('BIRTHDAY', 'Init-ChannelID', str(channel.id))
            self.config.set('BIRTHDAY', 'Announce-ChannelID', str(a_channel.id))
            self.config.set('BIRTHDAY', 'Announce-ChannelName', str(a_channel.name))
            self.config.set('BIRTHDAY', 'channelSet', 'True')
        else:
            embed = discord.Embed(description=f"The BirthdayChannel was not set",
                                  colour=discord.Colour(0xbf212f))
            await embedctx.edit(embed=embed)
            return embedctx
        return embedctx


def configset(config, name, settings):
    for key, data in settings.items():
        config.set(name, key, data)
    return config


def get_date_month(args):
    bstring = str(args)

    if '-' in args:
        args = bstring.split("-", 1)
    elif ' ' in args:
        args = bstring.split(" ", 1)
    else:
        return '', '', True

    if args[0].isnumeric():
        day = args[0]
        month = args[1]
    else:
        day = args[1]
        month = args[0]
    return day, month, False


def find_month(month):
    months_in_year = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
    index = 0
    for m in months_in_year:
        if re.search(month, m, re.IGNORECASE):
            index = months_in_year.index(m) + 1
            return m, index


def non_match_elements(list_a, list_b):
    non_match = []
    for i in list_a:
        if i not in list_b:
            non_match.append(i)
    return non_match


def setup(bot):
    bot.add_cog(Birthday(bot))
