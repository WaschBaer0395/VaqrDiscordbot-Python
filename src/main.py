'''
MIT License

Copyright (c) 2017-2018 Cree-Py

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import asyncio
import inspect
import math
import os
import sys
import traceback


import discord
from src.ext import utils
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='v!')

path = 'cogs.'
extensions = [x.replace('.py', '') for x in os.listdir(os.getcwd()+'/src/cogs/') if x.endswith('.py')]


def load_extension(cog, __path='cogs.'):
    members = inspect.getmembers(cog)
    for name, member in members:
        if name.startswith('on_'):
            bot.add_listener(member, name)
    try:
        bot.load_extension(f'{__path}{cog}')
    except Exception as e:
        print(f'LoadError: {cog}\n{type(e).__name__}: {e}')


def load_extensions(cogs, _path='cogs.'):
    for cog in cogs:
        load_extension(cog, _path)


load_extensions(extensions)
version = "v1.0.0"


async def send_cmd_help(ctx):
    cmd = ctx.command
    em = discord.Embed(title=f'Usage: {ctx.prefix + cmd.signature}')
    em.description = cmd.help
    return em


@bot.event
async def on_command_error(ctx, error):

    send_help = (commands.MissingRequiredArgument, commands.BadArgument, commands.TooManyArguments, commands.UserInputError)

    if isinstance(error, commands.CommandNotFound):  # fails silently
        pass

    if isinstance(error, send_help):
        _help = await send_cmd_help(ctx)
        await ctx.send(embed=_help)

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'```This command is on cooldown. Please wait {error.retry_after:.2f}s```')

    # if command has local error handler, return
    if hasattr(ctx.command, 'on_error'):
        return

    # get the original exception
    error = getattr(error, 'original', error)

    if isinstance(error, commands.BotMissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = '```I need the **{}** permission(s) to run this command.```'.format(fmt)
        await ctx.send(_message)
        return

    if isinstance(error, commands.DisabledCommand):
        await ctx.send('```This command has been disabled.```')
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("```This command is on cooldown, please retry in {}s.```".format(math.ceil(error.retry_after)))
        return

    if isinstance(error, commands.MissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = '```You need the **{}** permission(s) to use this command.```'.format(fmt)
        await ctx.send(_message)
        return

    if isinstance(error, commands.UserInputError):
        await ctx.send("```Invalid input.```")
        await ctx.send_command_help(ctx)
        return

    if isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send('```This command cannot be used in direct messages.```')
        except discord.Forbidden:
            pass
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send("```You do not have permission to use this command.```")
        return

    # ignore all other exception types, but print them to stderr
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)

    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def format_command_help(ctx, cmd):
    '''Format help for a command'''
    color = discord.Color.green()
    em = discord.Embed(color=color, description=cmd.help)

    if hasattr(cmd, 'invoke_without_command') and cmd.invoke_without_command:
        em.title = f'`Usage: {ctx.prefix}{cmd.signature}`'
    else:
        em.title = f'`{ctx.prefix}{cmd.signature}`'

    return em


@bot.command()
async def ping(ctx):
    '''Pong! Get the bot's response time'''
    em = discord.Embed(color=discord.Color.green())
    em.title = "Pong!"
    em.description = f'{bot.latency * 1000} ms'
    await ctx.send(embed=em)


@bot.command(hidden=True)
@utils.developer()
async def reload(ctx, cog):
    """Reloads a cog"""
    if cog.lower() == 'all':
        for cog in extensions:
            try:
                bot.unload_extension(f"cogs.{cog}")
            except Exception as e:
                await ctx.send(f"An error occured while reloading {cog}, error details: \n ```{e}```")
        load_extensions(extensions)
        return await ctx.send('All cogs updated successfully :white_check_mark:')
    if cog not in extensions:
        return await ctx.send(f'Cog {cog} does not exist.')
    try:
        bot.unload_extension(f"cogs.{cog}")
        await asyncio.sleep(1)
        load_extension(cog)
    except Exception as e:
        await ctx.send(f"An error occured while reloading {cog}, error details: \n ```{e}```")
    else:
        await ctx.send(f"Reloaded the {cog} cog successfully :white_check_mark:")

bot.run(TOKEN)
