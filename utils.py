from datetime import datetime

import aiofiles
import discord
from bing_image_downloader import downloader


async def get_member(guild, member_id):
    # Primary method
    member = guild.get_member(member_id)
    if member is not None:
        return member

    # Secondary method
    for member in guild.members:
        if str(member.id) == str(member_id):
            return member

    # If can't find member, refresh member lists and retry
    async for member in guild.fetch_members():
        if member.id == member_id:
            return member

    # If all else fails, return None
    return None


async def get_channel_named(guild, channel_name):
    for channel in guild.channels:
        if channel.name == channel_name:
            return channel


async def log(client, string, timestamp=True):
    # Log to stdout
    timestamp_string = ''
    if timestamp:
        timestamp_string = f'[{str(datetime.now())[:-7]}]'
    print(timestamp_string + ' ' + string)

    # Log to channel
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == 'bot-logs':
                try:
                    await channel.send(string)
                except discord.errors.HTTPException as e:
                    pass

    # Log to file
    try:
        async with aiofiles.open('log', mode='r') as f:
            previous_logs = await f.readlines()
    except FileNotFoundError:
        previous_logs = []

    async with aiofiles.open('log', mode='w') as f:
        for line in previous_logs:
            await f.write(line.strip() + '\n')
        await f.write(timestamp_string + ' ' + string + '\n')


async def download_corgis(client, ctx, amount):
    await ctx.send(f'Downloading {amount} images')
    downloader.download('corgis',
                        limit=amount,
                        output_dir='dogs',
                        adult_filter_off=False,
                        force_replace=False)
    await log(client, f'{ctx.author} ran /downloadcorgis {amount} in #{ctx.channel}')


async def confirmation(client, ctx, confirm_string='confirm'):
    # Ask for confirmation
    await ctx.send(f'Enter `{confirm_string}` to confirm action')

    # Wait for confirmation
    msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    if msg.content == confirm_string:
        await ctx.send(f'Action confirmed, executing')
        return True
    else:
        await ctx.send(f'Confirmation failed, terminating execution')
        return False


async def dm(member, content):
    channel = await member.create_dm()
    await channel.send(content)
