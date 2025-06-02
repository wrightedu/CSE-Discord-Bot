import re
import datetime
import aiofiles
import discord
from discord.ext import commands
from bing_image_downloader import downloader
# import time

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

    await interaction.followup.send(f'Downloading {amount} images')
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

async def update_view(interaction, view:discord.ui.View):
    """Takes in a view and updates the current message with the new view
    Uses the interaction to get the channel and message id. Fetches the message and edits it with the new view.

    Args:
        interaction (discord.Interaction): The interaction object
        view (discord.ui.View): The new view that will replace the old view
    """
    channel = interaction.channel
    message_id = interaction.message.id

    message = await channel.fetch_message(message_id)
    await message.edit(view=view)

async def get_time_epoch():
    """ Function that gets the current epoch timestamp.

    Returns:
        current_time (float): current epoch time as float
    """
    current_time = datetime.datetime.now()

    return current_time.timestamp()

async def get_string_from_epoch(time):
    """ Function that takes a total epoch time and converts it to so many minutes or hours

    Args:
        time (float): total epoch timestamp

    Returns:
        prompt (string): string equivalent of total epoch
    """

    string_return = ""
    hours = int((time) // 3600 % 24)
    minutes = int(time % 3600 // 60)

    if hours >= 1:
        string_return = f"{hours} hour" + ("s, " if hours > 1 else ", ")

    string_return += f"{minutes} minute" + ("s" if (minutes > 1 or minutes == 0) else "")

    return string_return

def get_last_pay_period_monday(current_date:str):
    """
    Takes unix date in string format and returns the week day
    current_date = unixtime
    datetime object

    returns the first monday's date of the last pay period
    """
    dt =  datetime.datetime.fromtimestamp(current_date)
    current_week_number= dt.isocalendar().week
    monday_date = None
    if current_week_number % 2 == 0:
        monday_date = get_monday(dt)
    else:
        one_week_before = dt - datetime.timedelta(weeks=1)
        monday_date = get_monday(one_week_before)
    return monday_date

def get_monday(date_now):
    """takes a datetime object date_now and gets the difference between the day 
    and starting day(monday of the week) and returns the date for monday"""

    weekday = date_now.isoweekday()
    days_to_substract = weekday - 1
    first_iso_monday = date_now - datetime.timedelta(days= days_to_substract)
    return first_iso_monday.date()


def get_unix_time(desired_date: str):
    """takes in a Data MM-DD-YYYY format and returns a Unix time stamp"""

    datetime_obj = datetime.datetime.strptime(desired_date, "%m-%d-%Y")
    unix_desired_date = datetime_obj.timestamp()
    return unix_desired_date


def result_parser(all_records, total_hours, complete_pomodoros):
    """takes in a Data MM-DD-YYYY format and returns the timesheet info in a pretty way. Returns completed pomodoros in pretty format.
        NOTE FOR FUTURE DEV: ONLY USE DURING THE REPORT FUNCTION"""
    # Formatting all_records
    timesheet_response = []
    for record in all_records:
        # print(record[2],  record[3])
        start_time_formatted = datetime.datetime.fromtimestamp(float(record[2])).strftime('%Y-%m-%d %H:%M:%S')
        end_time_formatted = datetime.datetime.fromtimestamp(float(record[3])).strftime('%Y-%m-%d %H:%M:%S') if record[3] is not None else 0
        total_hours_logged = record[4]/3600 if record[4] is not None else 0
        timesheet_response.append(f"Start Time: {start_time_formatted}\nEnd Time: {end_time_formatted}\n Hours Logged: {total_hours_logged:.3f}")

    # Fomatting total_hours
    if total_hours[0][0] is None:
        total_seconds = 0
    else:
        total_seconds = int(total_hours[0][0])
        # print(total_secods)

    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    total_hours_formatted = f"{hours}h {minutes}m"

    # Formatting complete_pomodoros
    pomodoro_response = []
    for pomodoro in complete_pomodoros:
        # print(pomodoro[2], pomodoro[3])
        time_spent_formatted = datetime.datetime.fromtimestamp(float(pomodoro[3])).strftime('%H:%M:%S') if pomodoro[3] is not None else 0
        pomodoro_response.append(f"Issue: {pomodoro[2]}\nTime Spent: {time_spent_formatted}\n")

    response_message = "Timesheets:\n"
    response_message += "\n\n".join(timesheet_response)
    response_message += f"\n\n\nTotal Hours: {total_hours_formatted}\n\n\n"
    response_message += f'Complete Pomodoros:\n'
    response_message += f"\n".join(pomodoro_response)
    
    return response_message

async def change_checkin_status(bot: commands.Bot, user_id: int, display_name: str, status: str):
    """ Function that changes the status of a CSE Dev Team member in checkin

    Args:
        bot (commands.Bot): a Discord bot object
        user_id (int): ID of Discord user that triggered change
        display_name (str): Display name of user that triggered change
        status (str): The status to set
    """

    # Find Guilds to watch
    guild = None
    for temp_guild in bot.guilds:
        if any(name in temp_guild.name for name in ['WSU CSE-EE Department', 'CSE Testing Server']):
            guild = temp_guild

    # If guild was found
    if guild is not None:
        # Get member object
        member = guild.get_member(user_id)

        # Get role object
        role = discord.utils.get(guild.roles, name="cse-devteam")

        # See if user has role
        if role is not None and role in member.roles:
            status_emojis = {
                "checkin": "🟢",
                "pomodoro": "🟠",
                "checkout": "🔴",
            }

            # Get checkin channel
            channel = discord.utils.get(guild.channels, name='checkin')

            # If channel is found
            if channel is not None:
                # Set message to assign
                message = None

                # Loop through ten most recent messages
                async for temp_message in channel.history(limit=10, oldest_first=False):
                    # If message has embeds
                    if len(temp_message.embeds) == 1:
                        # If embed is the embed we're looking for, set message
                        if temp_message.embeds[0].title == 'CSE Development Team Status':
                            message = temp_message
                            break
                
                # If message was not found, create it
                embed = discord.Embed(title="CSE Development Team Status")
                if message is None:
                    # Update description of new embed
                    embed.description = f"```{display_name} - {status_emojis[status]}```"

                    await channel.send(embed=embed)
                # If message found, update it
                else:
                    # Update description of embed
                    embed.description = message.embeds[0].description

                    # If user is inside of embed already, update them
                    if display_name in embed.description:
                        # Remove all markdown ticks
                        embed.description = embed.description.replace("```", "")

                        # Replace description
                        embed.description = re.sub(fr"({display_name} - )\S+(\s*$)", rf"\1{status_emojis[status]}\2", embed.description, flags=re.MULTILINE)

                        # Readd markdown ticks
                        embed.description = "```" + embed.description + "```"

                        # Edit message
                        await message.edit(embed=embed)
                    # If user isn't in embed, add them
                    else:
                        # Remove trailing characters
                        embed.description = embed.description.rstrip("`")

                        # Remove placeholder if necessary
                        embed.description = embed.description.replace("No members currently logged in", "")

                        # Add spacing if needed
                        if embed.description != '```':
                            embed.description += "\n"

                        # Add user and end code block
                        embed.description += f"{display_name} - {status_emojis[status]}```"

                        # Update message
                        await message.edit(embed=embed)
