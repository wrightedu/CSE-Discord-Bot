import re
from datetime import datetime

import aiofiles
import discord
from bing_image_downloader import downloader


<<<<<<< HEAD
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


=======
>>>>>>> parent of e94e7d0... Quick Commit for an update on ServerManagment Cog, as well as an update
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


async def create_role_menu(client, guild, reaction_roles):
    def get_emoji(emoji_name):
        emoji = discord.utils.get(client.emojis, name=emoji_name)
        if emoji is not None:
            return emoji
        return f':{emoji_name}:'

    # Get this guild's reaction roles
    guild_reaction_roles = reaction_roles[guild.id]

    # Generate list of menus to iterate through when sending messages
    menus = []
    for key in guild_reaction_roles[1].keys():
        menus.append((key, guild_reaction_roles[1][key]))

    # Generate each menu independently
    reaction_message_ids = []
    for menu in menus:
        # Get channel object
        channel_name = menu[1]['channel_name']
        reaction_role_channel = None
        for channel in guild.channels:
            if channel.name.strip().lower() == channel_name.strip().lower():
                reaction_role_channel = channel

        # Clear channel if necessary
        if bool(menu[1]['clear_channel']):
            await reaction_role_channel.purge(limit=99999999999999)

        # Send menus
        message = f'__**{menu[0].strip()}**__\n'
        if not bool(menu[1]['clear_channel']):
            message = f'_ _\n__**{menu[0].strip()}**__\n'
        for option_name in menu[1].keys():
            if option_name not in ['channel_name', 'clear_channel']:
                emoji = str(get_emoji(menu[1][option_name]['emoji']))
                message += f'{emoji} `{option_name}`\n'
        reaction_message = await reaction_role_channel.send(message)

        # React to menu
        for option_name in menu[1].keys():
            if option_name not in ['channel_name', 'clear_channel']:
                emoji = get_emoji(menu[1][option_name]['emoji'])
                await reaction_message.add_reaction(emoji)

            # Put reaction message ids in global list
            reaction_message_ids.append(reaction_message.id)
    return reaction_message_ids


async def build_server_helper(client, ctx, reaction_roles):
    guild = ctx.guild

    # Builds new class channels/categories from reaction roles
    class_names = re.compile('\\w{2,3} \\d{4}')
    guild_reaction_roles = reaction_roles[guild.id][1]

    # List all categories that will be created and get confirmation before actually creating
    creation_list_message = 'The following categories will be created:\n'
    for menu in guild_reaction_roles:
        for _class in guild_reaction_roles[menu]:
            if class_names.match(_class):
                class_number = guild_reaction_roles[menu][_class]['role']
                creation_list_message += class_number + '\n'
    await ctx.send(creation_list_message)

    if await confirmation(client, ctx, 'build'):
        # Iterate through all menus in reaction roles
        for menu in guild_reaction_roles:
            # Iterate through all classes in each menu
            for _class in guild_reaction_roles[menu]:
                # Ignore menu properties
                if class_names.match(_class):

                    class_number = guild_reaction_roles[menu][_class]['role']

                    # Check if category for class already exists (cross-listed). If so, don't make role or category
                    category_exists = False
                    for category in guild.categories:
                        if category.name == class_number:
                            category_exists = True

                    if not category_exists:
                        # Create class role
                        permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
                        await guild.create_role(name=class_number.replace(' ', ''), permissions=permissions)

                        # Create category
                        category = await guild.create_category(class_number)
                        await category.set_permissions(guild.default_role, read_messages=False)
                        for role in guild.roles:
                            if role.name == class_number.replace(' ', ''):
                                await category.set_permissions(role, read_messages=True)
                                break

                        # Create channels
                        text_channel = await category.create_text_channel(class_number.replace(' ', ''))
                        await text_channel.edit(topic=_class)
                        await category.create_voice_channel('Student Voice')
                        await category.create_voice_channel('TA Voice', user_limit=2)


async def destroy_server_helper(client, ctx):
    guild = ctx.guild

    # Deletes all class channels/categories
    class_names = re.compile('\\w{2,3} \\d{4}')
    role_names = re.compile('\\w{2,3}\\d{4}')

    # List all categories that will be deleted and get confirmation before actually deleting
    deletion_list_message = 'The following categories will be deleted:\n'
    for category in guild.categories:
        if class_names.match(category.name):
            deletion_list_message += category.name + '\n'
    await ctx.send(deletion_list_message)

    if await confirmation(client, ctx, 'destroy'):
        # Find all matching categories in the guild
        for category in guild.categories:
            if class_names.match(category.name):

                # Delete all channels in the category
                for channel in category.channels:
                    await channel.delete()

                # Delete the category itself
                await category.delete()

        # Delete class roles
        for role in guild.roles:
            if role_names.match(role.name):
                await role.delete()


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
