import discord
from discord.ext import commands

from ext.config import save_config, check_config
from ext.confirmer import ConfirmerSession

bot = commands.Bot('')


class Roles(commands.Cog):

    def __init__(self, _bot):
        """Cog to manage Roles adding and removing by pressing buttons."""
        self.bot = _bot

    @commands.command(aliases=['rinit', 'initroles', 'initr'])
    async def rolesinit(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """<Channel> Setup the channel to display Role selections."""
        if len(channel) == 1:
            try:
                conf, settings = check_config('ROLES', None)
                if settings.get('channelset') == 'True':
                    channelid = settings.get('init-channelid')

                    embed = discord.Embed(description=f"The role channel is already set to: \n"
                                                      f"<#{channelid}> - id: `{channelid}`\n"
                                                      f"Do you want to reinitiate the channel to a new one?")
                    message = await ctx.send(embed=embed)
                    response, message = await ConfirmerSession(page=embed).run(message=message)
                    if response:
                        message = await setchannel(message=message, channel=channel)
                        embed = discord.Embed(description=f"The role channel was set to: \n"
                                                          f"<#{channel[0].id}> - id: `{channel[0].id}`")
                        await message.edit(embed=embed)
                    else:
                        embed = discord.Embed(description=f"The role channel was not set")
                else:
                    embed = discord.Embed(description=f"The role channel was set to: \n"
                                                      f"<#{channel[0].id}> - id: `{channel[0].id}`")
                    message = await ctx.send(embed=embed)
                    message = await setchannel(message=message, channel=channel)

                await message.edit(embed=embed)
            except Exception as e:
                await ctx.send('```' + str(e) + '```')
                return
        else:
            embed = discord.Embed(description=f"Wrong syntax!\n"
                                              f"```v!rolesinit <#channel>``` ")
            await ctx.send(embed=embed)


async def channel_set(message, channel, conf):
    embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78),
                          description="Are you sure you want to set the roles channel to:\n"
                                      "<#{}> ?".format(channel.id))
    response, message = await ConfirmerSession(page=embed).run(message=message)
    if response is True:
        conf.set('ROLES', 'Init-ChannelName', str(channel.name))
        conf.set('ROLES', 'Init-ChannelID', str(channel.id))
        conf.set('ROLES', 'channelSet', 'True')
    else:
        embed = discord.Embed(description=f"The roles channel was not set",
                              colour=discord.Colour(0xbf212f))
        await message.edit(embed=embed)
        return message, None
    return message, conf


def get_config():
    settings = {
        'channelSet': 'False',
        'Init-ChannelName': 'None',
        'Init-ChannelID': 'None',
    }
    return check_config('ROLES', settings)


async def setchannel(message, channel):
    conf, _ = get_config()
    embedctx, conf = await channel_set(message=message, channel=channel[0], conf=conf)
    save_config(conf)
    return embedctx


def setup(bot):
    bot.add_cog(Roles(bot))
