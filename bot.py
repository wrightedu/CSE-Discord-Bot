#!/usr/bin/env python
import os
import shutil
from datetime import datetime
from itertools import cycle
from random import randint
from sys import argv
from time import sleep

import discord
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix='/')


###### ================================== ######
######               Events               ######
###### ================================== ######

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('being developed'), status=None, afk=False)
    await log('Bot is online')


###### ================================== ######
######              Commands              ######
###### ================================== ######

@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} loaded')
    log(f'{extension} loaded')


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} unloaded')
    log(f'{extension} loaded')


@bot.command()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} reloaded')
    log(f'{extension} reloaded')


###### ================================== ######
######         Separate Functions         ######
###### ================================== ######

async def changeStatus(status):
    print('Changing status')
    await bot.change_presence(activity=discord.Game(status))


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
