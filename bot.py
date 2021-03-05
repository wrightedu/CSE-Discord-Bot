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
reaction_roles = {}
reaction_message_ids = []
start_time = time()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


@client.event
async def on_ready():
    global reaction_roles

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
    cog.reaction_message_ids = reaction_message_ids

    # Generate role menu
    try:
        await create_role_menu(guild)
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


@client.event
async def on_raw_reaction_add(payload):
    global reaction_roles

    try:
        if payload.message_id in reaction_message_ids:
            # Get guild
            guild_id = payload.guild_id
            guild = discord.utils.find(lambda g: g.id == guild_id, client.guilds)

            # Get guild reaction roles
            guild_reaction_roles = reaction_roles[guild_id][1]

            # Find a role corresponding to the emoji name.
            classes = []
            for menu in guild_reaction_roles.keys():
                for class_name in guild_reaction_roles[menu].keys():
                    if class_name not in ['channel_name', 'clear_channel']:
                        classes.append(guild_reaction_roles[menu][class_name])
            role = None
            for _class in classes:
                emoji = f':{_class["emoji"]}:'
                if emoji in str(payload.emoji):
                    role = discord.utils.find(lambda r: r.name == _class['role'].replace(' ', ''), guild.roles)

            # If role found, assign it
            if role is not None:
                member = await guild.fetch_member(payload.user_id)
                if not member.bot:  # Error suppression
                    # Get class name from role
                    await member.add_roles(role)
                    await dm(member, f'Welcome to {role}!')
                    await log(client, f'Assigned role {role} to {member}')
    except Exception:
        await log(client, 'Error suppressed, likely due to bot reacting to a role menu')


@client.event
async def on_raw_reaction_remove(payload):
    if payload.message_id not in reaction_message_ids:
        return

    # Get guild
    guild_id = payload.guild_id
    guild = discord.utils.find(lambda g: g.id == guild_id, client.guilds)

    # Get guild reaction roles
    guild_reaction_roles = reaction_roles[guild_id][1]

    # Find a role corresponding to the emoji name.
    classes = []
    for menu in guild_reaction_roles.keys():
        for class_name in guild_reaction_roles[menu].keys():
            if class_name not in ['channel_name', 'clear_channel']:
                classes.append(guild_reaction_roles[menu][class_name])
    role = None
    for _class in classes:
        emoji = f':{_class["emoji"]}:'
        if emoji in str(payload.emoji):
            role = discord.utils.find(lambda r: r.name == _class['role'].replace(' ', ''), guild.roles)

    # If role found, take it
    if role is not None:
        member = await guild.fetch_member(payload.user_id)
        await member.remove_roles(role)
        await dm(member, f'We\'ve taken you out of {role}')
        await log(client, f'Took role {role} from {member}')


if __name__ == '__main__':
    # Run bot from key given by command line argument
    client.run(TOKEN)
