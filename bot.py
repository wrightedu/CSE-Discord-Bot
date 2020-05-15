#!/usr/bin/env python
import os
from datetime import datetime
from sys import argv

import discord
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix='/')


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('being developed'), status=None, afk=False)
    await log('Bot is online')


@bot.event
async def on_command_error(ctx, error):
    author, message = ctx.author, ctx.message

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required arguement')
        await ctx.send_help()

    elif isinstance(error, commands.MissingRole):
        await ctx.send('Missing role')

    elif isinstance(error, commands.CommandInvokeError):
        cogExists = False
        cogName = ctx.message.content[ctx.message.content.find(' ') + 1:]
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                if filename[:-3] == cogName:
                    cogExists = True
        if cogExists:
            await ctx.send(f'Cog {cogName} is not loaded')
        else:
            await ctx.send(f'Cog {cogName} does not exist')

    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(error)

    else:
        await ctx.send(f'Unexpected error: {error}')
        print(error)


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)


if __name__ == '__main__':
    # Load all cogs
    for filename in os.listdir('cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')

    # Run bot from key given by command line argument
    bot.run(argv[1])
