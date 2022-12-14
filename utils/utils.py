import datetime

import aiofiles
import discord
from bing_image_downloader import downloader


async def confirmation(bot, interaction:discord.Interaction, confirm_string='confirm'):
    """Add a layer of security to sensitive commands by adding a confirmation step
    Send message to user informing what confirmation code is. Ensure the next message received is by the author
    of the origional command. If so, ensure said message is the proper confirmation code. If this is the case,
    execute action and return true. If not, inform user that the action failed and return false.
    
    Args:
        bot (discord.ext.commands.bot.Bot): The bot object
        confirm_string (str): The string that must be sent by user to confirm action. Automatically set to 'confirm'.

    Outputs:
        If confirmation is successful: Message to user confirming execution
        If confirmation is not successful: Message to user informing of termination of execution

    Returns:
        (bool): Whether or not the confirmation succeeded
    """

    # Ask for confirmation
    await interaction.channel.send(f'Enter `{confirm_string}` to confirm action')

    # Wait for confirmation
    msg = await bot.wait_for('message', check=lambda message: message.author == interaction.user)
    if msg.content == confirm_string:
        await interaction.channel.send(f'Action confirmed, executing')
        return True
    else:
        await interaction.channel.send(f'Confirmation failed, terminating execution')
        return False


async def download_corgis(bot, interaction, amount):
    """Download Corgi Pictures
    Send message to user informing them how many corgis will be downloaded. Use the downloader to download
    a specified amount of corgies into 'dogs' with a functioning adult filter. Log the event.

    Args:
        bot (discord.ext.commands.bot.Bot): The bot object
        amount (int): The number of corgi pictures being downloaded.

    Outputs:
        The amount of images downloaded

    Logs:
        Who sent command and the amount of pictures downloaded.
    """

    await interaction.response.send_message(f'Downloading {amount} images')
    downloader.download('corgis',
                        limit=amount,
                        output_dir='dogs',
                        adult_filter_off=False,
                        force_replace=False)
    await log(bot, f'{interaction.user} ran /downloadcorgis {amount} in #{interaction.channel}')


async def dm(member, content):
    """Send a direct message to another user.
    Create a dm channel between the user and intended recipient. Send the desired message from the user to the
    recipient through the new channel.

    Args:
        member (discord.Member): The member to receive the dm
        content (str): The contents of the message being sent

    Outputs:
        A message with content `content` to a DM with `member`
    """

    channel = await member.create_dm()
    await channel.send(content)


async def get_channel_named(guild, channel_name):
    """Return a channel for use in other methods
    Loop through all the channels in the guild. If the channel matches the input channel name, return it.

    Args:
        channel_name (str): name of the channel being queried.

    Returns:
        channel (discord.channel.TextChannel): An instance of the channel being quieried
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


async def get_member(guild, member_id):
    """Return a member for use in other methods
    Try to get member from the member id passed in to the method. If this doesn't work, search through the list of
    all members and extract a matching member id. If this doesn't work, refresh member list and return member if the
    id matches the intended member id. If this doesn't work, return none.

    Args:
        member_id (int): id of the member

    Returns:
        member (discord.Member): An instance of the member being called for
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


async def log(bot, string, timestamp=True):
    """Save a record of events occuring within the server
    Save the current date and time as a string and print it. Loop through guilds in the bot, then for each
    guild search through all channels. If the channel name is 'bot-logs', send a log message there. Use
    Aiofiles to open log in read mode, and save previous logs. Use Aiofiles in write mode to append the log
    message to the document as well as the string.

    Args:
        bot (discord.ext.commands.bot.Bot): The bot object
        string (str): The message being sent to the log.
        timestamp (bool): Determine whether a timestamp will be given. Automatically set to true.
    """

    # Log to stdout
    timestamp_string = ''
    if timestamp:
        timestamp_string = f'[{str(datetime.datetime.now())[:-7]}]'
    print(timestamp_string + ' ' + string)

    # Log to channel
    for guild in bot.guilds:
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


def months_ago(months):
    """Gets the date and time a certain number of months ago
    Assumes 30 days in a month

    Returns:
        that_day (datetime): the date and time some months ago
    """

    num_days = months*30
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    that_day = now - delta
    return that_day
