import json

import discord
import configparser
from discord.ext import commands
from distutils.util import strtobool

channelSet = False
channelName = None
channelID = None
currentCount = None


class Counting(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['setcounting', 'setcount', 'setupcounting', 'countingchannel', 'sc'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def set_counting(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        '''Admin Only!!, setup counting channel'''
        if len(channel) > 1:
            await ctx.send('```counting can only be monitored in one Channel, please try again```')
            return
        else:
            config = check_config()
            if bool(strtobool(config.get('COUNTING', 'channelSet'))):
                msg = await ctx.send('```Are you sure that you want to reset the counting?```')
                custom_emoji = get(ctx.message.server.emojis, name="custom_emoji")
                reaction = await ctx.wait_for_reaction(['\N{SMILE}', custom_emoji], msg)
                await ctx.say("You responded with {}".format(reaction.emoji))
            else:
                config.set('COUNTING', 'channelSet', str(True))
                config.set('COUNTING', 'Name', str(channel[0].name))
                config.set('COUNTING', 'ID', str(channel[0].id))
                config.set('COUNTING', 'currentCount', str(0))
                try:
                    with open('settings.ini', 'w+') as configfile:
                        config.write(configfile)
                except Exception as e:
                    await ctx.send('```' + str(e) + '```')

            await ctx.send('```choosen channel is: ' + channel[0].name + '\n \
            with the following id: ' + str(channel[0].id) + '```')


def check_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # checking for existing config
    if config.has_section('COUNTING'):
        channelName = config.get('COUNTING', 'Name')
        channelID = commands.Bot(config.get('COUNTING', 'ID'))
        currentCount = commands.Bot(config.get('COUNTING', 'currentCount'))
        channelSet = commands.Bot(config.get('COUNTING', 'channelSet'))
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


def setup(bot):
    bot.add_cog(Counting(bot))
