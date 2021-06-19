#!/usr/bin/env python3
import os
from os.path import exists
from time import time

import discord
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv

from utils import *

intents = discord.Intents(messages=True, guilds=True, members=True)
client = commands.Bot(command_prefix='-', intents=intents)
start_time = time()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


@client.event
async def on_ready():
    # Set up Discord Components
    DiscordComponents(client)

    # Startup status
    await client.change_presence(activity=discord.Game('Booting'), status=discord.Status.dnd)

    # Start logging
    await log(client, '\n\n\n\n\n', False)
    await log(client, '###################################')
    await log(client, '# BOT STARTING FROM FULL SHUTDOWN #')
    await log(client, '###################################')

    # Startup status
    await client.change_presence(activity=discord.Game('Building servers'), status=discord.Status.idle)

    # Load all cogs
    await client.change_presence(activity=discord.Game(f'Loading Cogs'), status=discord.Status.idle)
    for file in os.listdir('Cogs'):
        if not file.startswith('__') and file.endswith('.py'):
            try:
                client.load_extension(f'Cogs.{file[:-3]}')
                await log(client, f'Loaded cog: {file[:-3]}')
            except commands.errors.NoEntryPointError:
                pass

    # Show the bot as online
    await client.change_presence(activity=discord.Game('Raider Up!'), status=discord.Status.online, afk=False)
    await log(client, 'Bot is online')

    # Print startup duration
    await log(client, '#########################')
    await log(client, '# BOT STARTUP COMPLETED #')
    await log(client, '#########################\n')
    await log(client, f'Started in {round(time() - start_time, 1)} seconds')


@client.event
async def on_command_error(ctx, error):
    author, message = ctx.author, ctx.message.content

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required arguement')
        await ctx.send_help()
        await log(client, f'{author} attempted to run `{message}` but failed because they were missing a required argument')

    elif isinstance(error, commands.MissingRole):
        await ctx.send('Missing role')
        await log(client, f'{author} attempted to run `{message}` but failed because they were missing a required role')

    elif isinstance(error, commands.CommandNotFound):
        await log(client, f'{author} attempted to run `{message}` but failed because the command was not found')

    else:
        await ctx.send(f'Unexpected error: {error}')
        await log(client, f'{author} attempted to run `{message}` but failed because of an unexpected error: {error}')


if __name__ == '__main__':
    # Run bot from key given by command line argument
    client.run(TOKEN)
