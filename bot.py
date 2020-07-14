#!/usr/bin/env python
import json
import os
from datetime import datetime
from os.path import exists
from pathlib import Path
from random import randint
from sys import argv
from time import sleep

import discord
from bing_image_downloader import downloader
from discord.ext import commands


##### ======= #####
##### GLOBALS #####
##### ======= #####
client = discord.Client()
client = commands.Bot(command_prefix='/')
invites = {}
invites_json = None


##### =========== #####
##### CORE EVENTS #####
##### =========== #####
@client.event
async def on_ready():
    global invites_json
    # Get invite links
    for guild in client.guilds:
        invites[guild.id] = await guild.invites()
    await log('Invites synced')

    # Load JSON
    with open('invites.json', 'r') as f:
        invites_json = json.loads(f.read())
    await log('JSON loaded')

    # Show the bot as online
    await client.change_presence(activity=discord.Game('Refactoring...'), status=None, afk=False)
    await log('Bot is online')


@client.event
async def on_command_error(ctx, error):
    author, message = ctx.author, ctx.message

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required arguement')
        await ctx.send_help()

    elif isinstance(error, commands.MissingRole):
        await ctx.send('Missing role')

    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(error)

    else:
        await ctx.send(f'Unexpected error: {error}')
        print(error)


##### ================ #####
##### GENERAL COMMANDS #####
##### ================ #####
@client.command()
@commands.has_role('cse-support')
async def status(ctx, *, status):
    status = status.strip()
    if status.lower() == 'none':
        await client.change_presence(activity=None)
        await log(f'Custom status disabled')
    elif len(status) <= 128:
        await client.change_presence(activity=discord.Game(status))
        await log(f'Status changed to "{status}"')


@client.command()
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)} ms')


##### ======= #####
##### INVITES #####
##### ======= #####
@client.event
async def on_member_join(member):
    invites_before_join = invites[member.guild.id]
    invites_after_join = await member.guild.invites()

    # Figure out which invite link was used
    for invite in invites_before_join:
        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
            await log(f'Member {member.name} joined')
            await log(f'Invite Code: {invite.code}')
            invites[member.guild.id] = invites_after_join

            # Assign role (and notify if prospective student)
            for link in invites_json.keys():
                if invite.code in link:
                    role = discord.utils.get(member.guild.roles, id=invites_json[link]['roleID'])
                    await member.add_roles(role)
                    await log(f'{invites_json[link]["purpose"]} {member.name} has joined')

                    # If prospective student, message in Prospective Student General
                    prospective_student_general_channel_id = 702895094881058896
                    prospective_student_general_channel = client.get_channel(prospective_student_general_channel_id)
                    channel = client.get_channel(702895094881058896)
                    await channel.send(f'Hello, {member.mention}')
            break


##### ================ #####
##### STUDENT COMAMNDS #####
##### ================ #####
@client.command()
async def support(ctx):
    await ctx.send(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @ them or email them at cse-support.wright.edu')


@client.command()
async def corgme(ctx):
    # Check if corgis dir exists
    if not exists('corgis'):
        downloadcorgis(100)

    # Get images from directory
    images = []
    for path in Path('corgis').rglob('*.*'):
        images.append('corgis/corgi/' + path.name)

    # Pick a random image
    image = images[randint(0, len(images) - 1)]

    # Send image
    await ctx.send(file=discord.File(image))


##### ============== #####
##### ADMIN COMMANDS #####
##### ============== #####
@client.command()
@commands.has_role('cse-support')
async def clear(ctx, amount=''):
    if amount == 'all':
        await ctx.send(f'Clearing all messages from this channel')
        amount = 999999999999999999999999999999999999999999
    elif amount == '':
        await ctx.send(f'No args passed. Use `/clear AMOUNT` to clear AMOUNT messages. Use `/clear all` to clear all messages from this channel')
        return
    else:
        await ctx.send(f'Clearing {amount} messages from this channel')
    sleep(1)
    await ctx.channel.purge(limit=int(float(amount)) + 2)


@client.command()
@commands.has_role('cse-support')
async def downloadcorgis(ctx, amount):
    try:
        amount = int(amount)
        await ctx.send(f'Downloading {amount} images')
    except Exception:
        amount = 100
        await ctx.send(f'Invalid parameter, downloading {amount} images')
    downloader.download('corgi',
                        limit=amount,
                        output_dir='corgis',
                        adult_filter_off=False,
                        force_replace=False)


##### ================= #####
##### UTILITY FUNCTIONS #####
##### ================= #####
async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)


def find_invite_by_code(invite_list, code):
    for invite in invite_list:
        if invite.code == code:
            return invite


if __name__ == '__main__':
    # Run bot from key given by command line argument
    client.run(argv[1])
