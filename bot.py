#!/usr/bin/env python3
import asyncio
import json
import os
import random
import sys
from os.path import exists
from random import randint
from time import sleep, time

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import *

client = discord.Client()
client = commands.Bot(command_prefix='-')
start_time = time()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


@client.event
async def on_ready():
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

    # Initialize each guild
    await client.change_presence(activity=discord.Game(f'Building servers'), status=discord.Status.idle)
    reaction_roles = {}
    reaction_message_ids = {}
    for guild in client.guilds:
        await log(client, f'Initializing server: {guild}')

        # Load reaction roles JSONs
        reaction_roles_filename = f'reaction_roles_{guild.id}.json'

        # Load reaction roles from file
        if exists(reaction_roles_filename):
            with open(reaction_roles_filename, 'r') as f:
                reaction_roles[guild.id] = (guild, json.loads(f.read()))

    # Load reaction roles into ServerManagement cog
    cog = client.get_cog('ServerManagement')
    cog.reaction_roles = reaction_roles
    cog.reaction_message_ids[guild.id] = reaction_message_ids

    # Generate role menu
    try:
        cog.reaction_message_ids = await create_role_menu(client, guild, reaction_roles)
    except Exception:
        await log(client, f'    failed, no reaction roles JSON')

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
