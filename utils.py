from datetime import datetime

import aiofiles
import discord
from bing_image_downloader import downloader


async def get_member(guild, member_id):
    """Return a member for use in other methods
    Try to get member from the member id passed in to the method. If this doesn't work, search through the list of
    all members and extract a matching member id. If this doesn't work, refresh member list and return member if the
    id matches the intended member id. If this doesn't work, return none. 

    Args:
        member_id (int): id of the member

    Returns:
        member (Member): An instance of the member being called for
    """
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
    """Return a channel for use in other methods
    Loop through all the channels in the guild. If the channel matches the input channel name, return it.

    Args:
        channel_name (str): name of the channel being quiered. 
    
    Returns:
        channel (Union[abc.GuildChannel, Object]): An instance of the channel being quieried
    """
    for channel in guild.channels:
        if channel.name == channel_name:
            return channel


async def get_emoji_named(guild, emoji_name):
    """Return an emoji for use in other methods.
    Search through all the emojis in the guild. If the name of one mathces the input emoji name, return it. 

    Args:
        emoji_name (str): name of the emoji being searched for

    Returns: 
        emoji (discord.Emoji): an instance of the emoji being quieried for.
    """
    for emoji in guild.emojis:
        if emoji.name == emoji_name:
            return emoji


async def log(client, string, timestamp=True):
    """Save a record of events occuring within the server
    Save the current date and time as a string and print it. Loop through guilds in the client, then for each
    guild search through all channels. If the channel name is 'bot-logs', send a log message there. Use
    Aiofiles to open log in read mode, and save previous logs. Use Aiofiles in write mode to append the log
    message to the document as well as the string. 
    
    Args:
        client (client): The client connection connected to Discord
        string (str): The message being sent to the log. 
        timestamp (bool): Determine whether a timestamp will be given. Automatically set to true. 
    """
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
    """Download Corgi Pictures
    Send message to user informing them how many corgis will be downloaded. Use the downloader to download
    a specified amount of corgies into 'dogs' with a functioning adult filter. Log the event.

    Args:
        client (client): The client connection connected to Discord 
        amount (int): The number of corgi pictures being downloaded. 

    Logs:
        -Who sent command and the amount of pictures downloaded. 
    """
    await ctx.send(f'Downloading {amount} images')
    downloader.download('corgis',
                        limit=amount,
                        output_dir='dogs',
                        adult_filter_off=False,
                        force_replace=False)
    await log(client, f'{ctx.author} ran /downloadcorgis {amount} in #{ctx.channel}')


async def confirmation(client, ctx, confirm_string='confirm'):
    """Add a layer of security to sensitive commands by adding a confirmation step
    Send message to user informing what confirmation code is. Ensure the next message received is by the author
    of the origional command. If so, ensure said message is the proper confirmation code. If this is the case, 
    execute action and return true. If not, inform user that the action failed and return false. 
    Args:
        client (client): The client connection connected to Discord 
        confirm_string (str): The string that must be sent by user to confirm action. Automatically set to 'confirm'.

    Outputs:
        -If confirmation is successful: Message to user confirming execution
        -If confirmation is not successful: Message to user informing of termination of execution

    Returns:
        -(bool): A boolean value used to determine whether the action requesting confirmation may be completed
    """
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
    """Send a direct message to another user. 
    Create a dm channel between the user and intended recipient. Send the desired message from the user to the 
    recipient through the new channel. 
    Args:
        member (discord.Member): The member to receive the dm
        content (str): The contents of the message being sent
    """
    channel = await member.create_dm()
    await channel.send(content)
