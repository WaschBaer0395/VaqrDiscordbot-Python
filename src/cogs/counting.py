import json

import discord
import configparser
from discord.ext import commands
from distutils.util import strtobool

from ext.confirmer import ConfirmerSession

channelSet = False
channelName = None
channelID = None
currentCount = None

bot = commands.Bot('')


class Counting(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['setcounting', 'setcount', 'setupcounting', 'countingchannel', 'sc'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def set_counting(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        '''Admin Only!!, setup counting channel'''
        if len(channel) > 1:
            await ctx.send( discord.Embed(description=f"Counting can only be applied in 1 channel. Please try again.",
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
                    if int(config.get('COUNTING', 'currentCount'))+1 == int(message.content):
                        config.set('COUNTING', 'currentCount', message.content)
                        save_config(config)
                    else:
                        raise WrongCount
                else:
                    raise WrongCount
        except WrongCount:
            await message.delete()
            return


class WrongCount(Exception):
    pass


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


def setup(bot):
    bot.add_cog(Counting(bot))
