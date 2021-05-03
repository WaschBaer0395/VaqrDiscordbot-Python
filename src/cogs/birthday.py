import asyncio
import re
import discord


from discord.ext import commands, tasks
from ext.SQLlite import SqlLite
from ext.config import *
from ext.confirmer import ConfirmerSession
from datetime import datetime
from pytz import timezone

bot = commands.Bot('')


class Birthday(commands.Cog):

    def __init__(self, _bot):
        self.bot = _bot
        self.conf = None
        self.settings = None
        self.index = 0
        init_db()
        self.init_config()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_time.start()

    def init_config(self):
        settings = {
                'channelSet': 'False',
                'Init-ChannelName': 'None',
                'Init-ChannelID': 'None',
                'Announcetime': '8:00am',
                'Announcetimezone': 'US/Pacific',
                'Announce-ChannelID': 'None',
                'Announce-ChannelName': 'None',
                'BirthdayRole': 'None',
                'SingularMessage': 'Has their Birthday today, wish them a happy birthday!',
                'PluralMessage': 'Have their Birthday today, wish them a happy birthday!'
        }
        self.conf, self.settings = check_config('BIRTHDAY', settings)

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
                                               colour=discord.Colour(0x37b326)))
            return
        else:
            monthday = find_month(month)[0][:3] + '-' + day
            add_birthday(ctx.author, monthday, find_month(month)[1], day)
            await ctx.send(embed=discord.Embed(description=f"Your Birthday was set for: `{day}-{find_month(month)[0]}`\n"
                                                           f"Birthdays will always be announced at"
                                                           f" {self.conf.get('BIRTHDAY', 'Announcetime')}"
                                                           f" {self.conf.get('BIRTHDAY', 'Announcetimezone')}",
                                               colour=discord.Colour(0x00FF97)))

    @commands.command()
    async def btime(self, ctx, *, arg=''):
        '''<Time> Setup the Announce Time'''
        in_time = ''
        try:
            in_time = datetime.strptime(arg, "%I:%M %p")
        except ValueError:
            try:
                in_time = datetime.strptime(arg, "%I:%M%p")
            except ValueError:
                try:
                    in_time = datetime.strptime(arg, "%I %p")
                except ValueError:
                    try:
                        in_time = datetime.strptime(arg, "%I%p")
                    except ValueError:
                        await ctx.send(embed=discord.Embed(
                            description=f"Error Setting time\n"
                                        f"Enter a correct time with either of those formats:\n"
                                        f"example `8am`, `8 am`, `08am`, `08 am`, "
                                        f"`8:00am`, `8:00 am`, `08:00 am`, `08:00am`",
                            colour=discord.Colour(0x37b326)))
                        return
        if int(in_time.minute%10) == 0:
            conv_time = in_time.strftime('%I:%M%p')
            self.conf.set('BIRTHDAY', 'AnnounceTime', conv_time)
            save_config(self.conf)
            await ctx.send(embed=discord.Embed(
                description=f"Announcetime has been set to `{conv_time}`",
                colour=discord.Colour(0x00FF97)))
        else:
            await ctx.send(embed=discord.Embed(
                description=f"Time can only be entered with Minutes being a multiple of 10 !`\n"
                            f"e.g: 10 20 30 40 50 0",
                colour=discord.Colour(0x37b326)))
            return

    @commands.command()
    async def brole(self, ctx, role: commands.Greedy[discord.Role]):
        '''<@Role> Setup your Birthdayrole'''

        if len(role) == 0 or len(role) > 1 or type(role[0]) != discord.Role:
            await ctx.send(embed=discord.Embed(description=f"Syntax is `bset <@role>`\n"
                                                           f"the role entered is either not a role\n"
                                                           f" or you entered more than 2 Roles",
                                               colour=discord.Colour(0x37b326)))
        else:
            self.conf.set('BIRTHDAY', 'BirthdayRole', str(role[0].id))
            save_config(self.conf)
            await ctx.send(embed=discord.Embed(description=f"Role has been set to <@&{str(role[0].id)}>\n",
                                               colour=discord.Colour(0x00FF97)))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def bforcedel(self, ctx, member: commands.Greedy[discord.Member]):
        '''<user> Force Delete a birthday'''
        del_birthday(member[0].id)
        await ctx.send(embed=discord.Embed(description=f"Birthday for : <@{member[0].id}>, was deleted",
                                           colour=discord.Colour(0x00FF97)))
        return

    @commands.command()
    async def bdel(self, ctx):
        '''Delete your birthday from the DB'''
        del_birthday(ctx.author.id)
        await ctx.send(embed=discord.Embed(description=f"Your Birthday was deleted",
                                           colour=discord.Colour(0x00FF97)))
        return

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def binit(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        '''<commandChannel> <announceChannel> Setup Birthday Channel'''
        if len(channel) != 2:
            await ctx.send(embed=discord.Embed(description=f"Syntax is `bset <birthdaychannel> <Accouncementchannel>`\n"
                                                           f"you have either selected only 1, or more than 2 channels",
                                               colour=discord.Colour(0x37b326)))
            return
        else:
            try:
                embedctx = await self.channel_set(ctx, channel[0], channel[1])
                save_config(self.conf)
            except Exception as e:
                await ctx.send('```' + str(e) + '```')
                return
            embed = discord.Embed(description=f"The Birthday-Command Channel was set to: \n"
                                              f"<#{channel[0].id}> -`{channel[0].id}`"
                                              f"\n"
                                              f"The Birthday-Announce Channel was set to: \n"
                                              f"<#{channel[1].id}> -`{channel[1].id}`\n"
                                              f"Dont forget to also set:\n"
                                              f"the announce time with `btime`\n"
                                              f"the role with `brole`\n"
                                              f"and maybe change the announce message with `bmsgp` for plural\n"
                                              f"and `bmsg` for singular", colour=discord.Colour(0x00FF97))
            await embedctx.edit(embed=embed)

    @commands.command()
    async def bmsgp(self, ctx, *, arg=''):
        self.conf.set('BIRTHDAY', 'PluralMessage', arg)
        save_config(self.conf)
        await ctx.send(embed=discord.Embed(description=f"Message has been set to: \n"
                                                       f"<user>, <user> and <user>, {arg} <here>",
                                           colour=discord.Colour(0x00FF97)))

    @commands.command()
    async def bmsg(self, ctx, *, arg=''):
        self.conf.set('BIRTHDAY', 'SingularMessage', arg)
        save_config(self.conf)
        await ctx.send(embed=discord.Embed(description=f"Message has been set to: \n"
                                                       f"<user>, {arg} <here>",
                                           colour=discord.Colour(0x00FF97)))

    def cog_unload(self):
        self.check_time.cancel()

    @tasks.loop(minutes=1)
    async def check_time(self):
        # This function runs periodically every 10minutes
        utc = timezone('UTC')
        utc_now = utc.localize(datetime.utcnow())
        user_time = utc_now
        user_date = utc_now
        if utc_now != datetime.now():
            user_tz = timezone(self.conf.get('BIRTHDAY', 'Announcetimezone'))
            user_date = user_time.astimezone(user_tz)
            user_time = user_time.astimezone(user_tz).strftime("%H:%M")

        in_time = datetime.strptime(self.conf.get('BIRTHDAY', 'Announcetime'), "%I:%M%p")
        out_time = datetime.strftime(in_time, "%H:%M")

        print('Check Time - Current: {} vs. User set: {}'.format(user_time, out_time))
        if user_time == out_time:
            await self.remove_birthday_flag()
            self.del_obs_members()
            found, birthday_kids = self.find_birthday(user_date)
            print('Birthdays checked at: ' + utc.localize(datetime.utcnow()).astimezone(timezone(
                self.conf.get('BIRTHDAY', 'Announcetimezone'))).strftime("%H:%M:%S.%fZ"))
            if found:
                await self.set_birthday_role(birthday_kids)
                await self.greet_birthday_kids(birthday_kids)

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

        channel = discord.utils.get(self.bot.guilds[0].channels, id=int(
                                    self.conf.get('BIRTHDAY', 'Announce-ChannelID')))
        if len(birthday_kids) > 1:
            #await channel.send(embed=discord.Embed(title='@here', description=f"{names} {self.conf.get('BIRTHDAY', 'PluralMessage')}",
            #                                       colour=discord.Colour(0x00FF97)))
            await channel.send(names + self.conf.get('BIRTHDAY', 'PluralMessage') + ' @here')
        else:
            #await channel.send(embed=discord.Embed(title='@here', description=f"{names} {self.conf.get('BIRTHDAY', 'SingularMessage')}",
            #                                       colour=discord.Colour(0x00FF97)))
            await channel.send(names + self.conf.get('BIRTHDAY', 'SingularMessage') + ' @here')

    def del_obs_members(self):
        statement = '''SELECT UserID FROM Birthday'''
        ret, data = SqlLite('Birthdays').execute_statement(statement)
        member_ids = []
        bday_ids = []
        for d in data:
            bday_ids.append(d[0])
        for m in self.bot.guilds[0].members:
            member_ids.append(m.id)

        non_match = non_match_elements(bday_ids, member_ids)
        if len(non_match) != 0:
            for d in non_match:
                del_birthday(d)

    def find_birthday(self, curr_date):
        statement = '''SELECT UserID FROM Birthday WHERE Day=? AND month=?'''
        args = (curr_date.day, curr_date.month)
        ret, data = SqlLite('Birthdays').execute_statement(statement, args)

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

    async def channel_set(self, ctx, channel, a_channel):
        embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78),
                              description="Are you sure you want to Set the BirthdayChannel ?")
        b_session = ConfirmerSession(ctx, page=embed)
        response, embedctx = await b_session.run()
        if response is True:
            self.conf.set('BIRTHDAY', 'Init-ChannelName', str(channel.name))
            self.conf.set('BIRTHDAY', 'Init-ChannelID', str(channel.id))
            self.conf.set('BIRTHDAY', 'Announce-ChannelID', str(a_channel.id))
            self.conf.set('BIRTHDAY', 'Announce-ChannelName', str(a_channel.name))
            self.conf.set('BIRTHDAY', 'channelSet', 'True')
        else:
            embed = discord.Embed(description=f"The BirthdayChannel was not set",
                                  colour=discord.Colour(0xbf212f))
            await embedctx.edit(embed=embed)
            return embedctx
        return embedctx

    async def remove_birthday_role(self, members_ids):
        role = self.bot.guilds[0].get_role(int(self.conf.get('BIRTHDAY', 'birthdayrole')))
        for m_id in members_ids[0]:
            member = self.bot.guilds[0].get_member(m_id)
            await member.remove_roles(role)

    async def set_birthday_role(self, birthday_kids):
        role = self.bot.guilds[0].get_role(int(self.conf.get('BIRTHDAY', 'birthdayrole')))
        for member in birthday_kids:
            set_birthday_flag(member.id)
            await member.add_roles(role)

    async def remove_birthday_flag(self):
        statement = '''SELECT UserID FROM Birthday WHERE Birthday=1'''
        ret, data = SqlLite('Birthdays').execute_statement(statement)
        if len(data) != 0:
            await self.remove_birthday_role(data)
            statement = '''UPDATE BIRTHDAY SET birthday=0 WHERE Birthday=1'''
            ret, err = SqlLite('Birthdays').execute_statement(statement)


def add_birthday(user, md, m, d):
    statement = ''' INSERT INTO Birthday 
                    (UserID,UserName,Discriminator,Nickname,MonthDayDisp,Month,Day,Timezone,Birthday)
                    VALUES(?,?,?,?,?,?,?,'',0)'''

    args = (str(user.id), user.name, user.discriminator, user.nick, md, str(m), str(d),)
    ret, err = SqlLite('Birthdays').execute_statement(statement, args)
    if 'UNIQUE' in str(err):
        ret = update_birthday(user, md, m, d)
    return ret


def set_birthday_flag(_id):
    statement = '''UPDATE BIRTHDAY SET Birthday=1 WHERE UserID=?'''
    args = (_id,)
    SqlLite('Birthdays').execute_statement(statement, args)


def del_birthday(userid):
    statement = ''' DELETE FROM Birthday WHERE UserID=?'''
    args = (str(userid),)
    ret, data = SqlLite('Birthdays').execute_statement(statement, args)
    return ret


def update_birthday(user, md, m, d):
    statement = ''' UPDATE Birthday SET MonthDayDisp=?,Month=?,Day=? WHERE UserID=?'''
    args = (md, m, d, user.id,)
    ret, err = SqlLite('Birthdays').execute_statement(statement, args)
    return ret


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


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()


def init_db():
    statement = ''' CREATE TABLE IF NOT EXISTS Birthday( \
                        UserID integer PRIMARY KEY, \
                        UserName text NOT NULL, \
                        Discriminator text NOT NULL, \
                        Nickname text, \
                        MonthDayDisp text, \
                        Month integer, \
                        Day integer, \
                        Timezone text, \
                        Birthday integer 
                        );'''
    SqlLite('Birthdays').create_table(statement)


def setup(bot):
    bot.add_cog(Birthday(bot))
