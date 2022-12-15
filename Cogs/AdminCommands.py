import os
import sys
from time import sleep
import re

from discord.ext import commands
from discord import MessageType
from discord import app_commands

from utils.utils import *


async def setup(bot:commands.Bot):
    await bot.add_cog(AdminCommands(bot))


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="-announce MSG to several #channels")
    @app_commands.default_permissions(administrator=True)
    async def announce(self, interaction:discord.Interaction, channel_mentions:str):
        """
        Uses the bot to announce something instead of having an admin to do so

        Args:
            channel_mentions (str): the channels to which the announcement is sent

        Outputs:
            The announcement to the specified channel(s) in the CSE server
            Logs that the specific user used the announcement command
        """

        # Gets the message from the user
        await interaction.response.send_message("Please enter a message.")
        message = await self.bot.wait_for("message", check=lambda message: message.author == interaction.user)

        # logs appropriately
        await log(self.bot, f"{interaction.user} has executed the announcement command in #{interaction.channel}")

        # gets the channel ids from the mentions
        channel_mentions_list = channel_mentions.split()
        channels = []
        channel_names = []
        for channel_mention in channel_mentions_list:
            # ensures the channel mentions can be converted to integers
            try:
                int(channel_mention[2:-1])
            except ValueError:
                await interaction.channel.send("The `channel_mentions` parameter can only take channel mentions (i.e. of format `#channel`).")
                await log(self.bot, f"{interaction.user} tried making an announcement from #{interaction.channel} but failed because of invalid channel mention(s)")
                return

            # ensures the channels exist
            channel = discord.utils.get(interaction.guild.text_channels, id=int(channel_mention[2:-1]))
            if (channel == None):
                await interaction.channel.send(f"The '{channel_mention}' channel could not be found. The `channel_mentions` parameter can only take channel mentions (i.e. of format `#channel`).")
                await log(self.bot, f"{interaction.user} tried making an announcement from #{interaction.channel} but failed because of invalid channel mention(s)")
                return
            channels.append(channel)
            channel_names.append(f"#{channel.name}")

        # sends the message to the specified channels
        for channel in channels:
            await channel.send(message.content)
        
        # logs appropriately
        await log(self.bot, f"{interaction.user} made an announcement from #{interaction.channel} to {', '.join(channel_names)}")


    @app_commands.command(description="clears either 'all' or the specified number of messages from the channel")
    @app_commands.default_permissions(administrator=True)
    async def clear(self, interaction:discord.Interaction, amount:str):
        """Clears a specific number of messages from a guild
        Take in user input for the number of messages they would like to get cleared. If the amount is 'all',
        clear a very large number of messages from the server. Otherwise, send message confirming how many
        messages are being cleared and log it. Purge the appropriate number of messages from the channel.

        Args:
            amount (str): Number of messages to be removed

        Outputs:
            States the amount of messages being cleared or, if invalid input, help on how to use the command
        """

        await interaction.response.defer(ephemeral=True)
        if amount == 'all':
            if not await confirmation(self.bot, interaction):
                await interaction.followup.send("Command not confirmed")
                return
            await interaction.channel.send(f'Clearing all messages from this channel')
            await log(self.bot, f'{interaction.user} cleared {amount} messages from #{interaction.channel}')
            amount = 999999999999999999999999999999999999999999

        else:
            try:
                amount = int(amount)
            except ValueError:
                await interaction.channel.send("The `amount` parameter can only take either `all` or a number.")
                await log(self.bot, f'{interaction.user} attempted to clear messages from #{interaction.channel}, but it failed because a valid "amount" was not passed')
                await interaction.followup.send("`amount` parameter is invalid")
                return

            if amount < 10:
                await interaction.channel.send(f'Clearing {amount} messages from this channel')
                await log(self.bot, f'{interaction.user} cleared {amount} messages from #{interaction.channel}')
                sleep(1)
                await interaction.channel.purge(limit=int(float(amount)) + 1)
                await interaction.followup.send(f'Cleared {amount} messages from this channel')
                return
            elif amount >= 10 and not await confirmation(self.bot, interaction):
                await interaction.followup.send("Command not confirmed")
                return
            await interaction.channel.send(f'Clearing {amount} messages from this channel')
            await log(self.bot, f'{interaction.user} cleared {amount} messages from #{interaction.channel}')

        sleep(1)
        await interaction.channel.purge(limit=int(float(amount)) + 4)
        await interaction.followup.send(f'Cleared {amount} messages from this channel')


    @app_commands.command(description="removes a specified role from each member of a guild.")
    @app_commands.default_permissions(administrator=True)
    async def clearrole(self, interaction:discord.Interaction, role_mention:str):
        """Remove a role from each member of a guild.
        Remove the extra characters from the ID number of the guild obtained from the role_mention. Search through every
        member of a guild to see if they have the role that matches the ID in question. If the member has the role,
        remove it from their roles. Send message in chat confirming that the role has been removed, and the number of
        users it has been removed from.

        Args:
            role_mention (str): mention of role being removed

        Outputs:
            Message to chat regarding what role was removed and how many users were stripped of it
        """

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Removing role")
        guild = interaction.guild

        try:
            int(role_mention[3:-1])
        except ValueError:
            await interaction.channel.send("The `role_mention` parameter can only take role mentions (i.e. of format `@role`).")
            await log(self.bot, f"{interaction.user} tried clearing the '{role_mention}' role in #{interaction.channel} but failed because of an invalid role mention")
            return

        role = discord.utils.get(guild.roles, id=int(role_mention[3:-1]))
        if role == None:
            await interaction.channel.send(f"The '{role_mention}' role could not be found. The `role_mention` parameter can only take role mentions (i.e. of format `@role`).")
            await log(self.bot, f"{interaction.user} tried clearing the '{role_mention}' role in #{interaction.channel} but failed because it could not be found")
            return

        cleared_members = []

        await log(self.bot, f"{interaction.user} is clearing the '@{role.name}' role from all members:")

        async for member in guild.fetch_members():
            if role in member.roles:
                await member.remove_roles(role)
                name = member.nick if member.nick is not None else member.name
                await log(self.bot, name, False)
                cleared_members.append(name)

        if len(cleared_members) > 10:
            await interaction.channel.send(f'Cleared {role.mention} from {len(cleared_members)} members')
        elif len(cleared_members) == 0:
            await interaction.channel.send(f'No members have the role {role.mention}')
        else:
            await interaction.channel.send(f'Cleared {role.mention} from {", ".join(cleared_members)}')

    @app_commands.command(description="downloads a given number of corgi pictures")
    @app_commands.default_permissions(administrator=True)
    async def downloadcorgis(self, interaction:discord.Interaction, amount:int):
        """Downloads a given number of corgi pictures.
        Convert user input to an integer. If this is not possible, set the amount of pictures as 100.
        Call the download_corgies method from utils.py. Log the user and number of images downloaded.

        Args:
            amount (int): Number of pictures/pieces of media being downloaded

        Outputs:
            Message to log stating the user that executed the command and how many images were downloaded
            Message to user stating numer of images downloaded
        """

        await download_corgis(self.bot, interaction, amount)
    

    @app_commands.command(description="outputs all messages from a specified user after a specified date with some metadata to a file")
    @app_commands.default_permissions(administrator=True)
    async def history(self, interaction:discord.Interaction, username:str):
        """Outputs all messages from a specified user after a specified date with some metadata to a file
        Prompts user for username and date. Outputs messages authored by that username and sent after that date
        to a file. Outputs file to discord channel if it is less that 4 MB.

        Args:
            username (str): username of the desired user (without # and 4 digits)
        Outputs:
            A file to chat including all messages from a user after a date, whether those messages are a reply,
            a link to those messages, and all reactions to those messages.
        """

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        member_found = False
        for member in guild.members:
            if member.name == username:
                member_found = True
                break

        if not member_found:
            await interaction.channel.send(f"That user is no longer active in the server. Would you like to continue this search query anyway?")
            if not await confirmation(self.bot, interaction, confirm_string="yes"):
                await interaction.followup.send("command not confirmed")
                return
        that_day = months_ago(4)
        
        history_file = open("/tmp/history.txt", "w")
        channel = interaction.channel
        # gets 250 most recent messages posted less than 4 months ago
        messages = [message async for message in channel.history(limit=250, after=that_day, oldest_first=False)]

        for message in messages:
            if message.author.name == username and message.type is MessageType.default:
                history_file.write(f"{message.content}\n")
                if message.reference:
                    history_file.write(f"a reply\n")
                else:
                    history_file.write(f"not a reply\n")
                history_file.write(f"{message.jump_url}\n")
                for reaction in message.reactions:
                    history_file.write(f"{reaction}\n")
                history_file.write(f"\n")

        history_file.close()

        size = os.path.getsize("/tmp/history.txt")
        if size == 0:
            await interaction.channel.send(f"No messages were found.")
        elif size <= 4194304:
            await interaction.channel.send(file=discord.File("/tmp/history.txt"))
        else:
            await interaction.channel.send(f"Error: The file is greater than 4 MB and will therefore not be output.")

        os.remove("/tmp/history.txt")
        await interaction.followup.send("History gathered")


    @app_commands.command(description="set status of discord bot")
    @app_commands.default_permissions(administrator=True)
    async def status(self, interaction:discord.Interaction, status:str):
        """Set status of discord bot
        Take in a user input for the status of the Discord Bot. If the status is 'none', log that the user
        removed the custom status. Otherwise, ensure proper length of message, and calls change_presence method
        on the discord bot and passes in the user input to the method. Log the author and new status.

        Args:
            status (str): Text to be displayed
        """

        await interaction.response.defer(ephemeral=True)

        # open a file to store the status in
        async with aiofiles.open('status.txt', mode='w') as f:
        
            status = status.strip()
            if status.lower() == 'none':
                await self.bot.change_presence(activity=None)
                await log(self.bot, f'{interaction.user} disabled the custom status')
                await f.write('Raider Up!') # Default status for when the bot restarts
            elif len(status) <= 128:
                await self.bot.change_presence(activity=discord.Game(status))
                await log(self.bot, f'{interaction.user} changed the custom status to "Playing {status}"')
                await f.write(status) # write the new status to the file
        await interaction.followup.send("Status set")
    
    
    @app_commands.command(description="outputs various stats of the server")
    @app_commands.default_permissions(administrator=True)
    async def stats(self, interaction:discord.Interaction):
        """Outputs various stats of the server
        Send message with server stats to user

        Outputs:
            Message to chat including total number of channels, text channels, voice channels, users, classes, roles,
            and people with top ten roles.
        """

        guild = interaction.guild

        embed = discord.Embed(
            title="Server Stats",
            description="Important Stats of the Server",
            color=discord.Color.green())

        total_text_channels = len(guild.text_channels)
        total_voice_channels = len(guild.voice_channels)
        total_channels = total_text_channels + total_voice_channels 
        total_users = len(interaction.guild.members)

        num_roles = 0
        for role in guild.roles:
            num_roles += 1
        
        num_classes = 0
        for category in guild.categories:
            class_name = re.search("^\w{2,3} \d{4}", category.name)
            if class_name != None:
                num_classes += 1

        embed.add_field(name="Total Channels: ", value=total_channels)
        embed.add_field(name="Text Channels: ", value=total_text_channels)
        embed.add_field(name="Voice Channels: ", value=total_voice_channels)
        embed.add_field(name="Max Channels: ", value=500)
        embed.add_field(name="Total Users: ", value=total_users)
        embed.add_field(name="Total Classes: ", value=num_classes)
        embed.add_field(name="Total Roles: ", value=num_roles)
        embed.add_field(name=chr(173), value=chr(173))
        embed.add_field(name=chr(173), value=chr(173))
        embed.add_field(name="Users with\nTop Roles", value='\u200b')
        embed.add_field(name=chr(173), value=chr(173))
        embed.add_field(name=chr(173), value=chr(173))
        
        roles_list = []
        for role in guild.roles:
            users_with_role = len(role.members)
            roles_list.append((role, users_with_role))
        
        top_roles = sorted(roles_list, key=lambda y: y[1], reverse=True)[1:]

        for index, value in enumerate(top_roles):
            if index > 9:
                break
            embed.add_field(name=value[0], value=value[1])

        await interaction.response.send_message(embed=embed)


    @app_commands.command(description="restart the discord bot")
    @app_commands.default_permissions(administrator=True)
    async def restart(self, interaction:discord.Interaction):
        """Restart the discord bot
        Send message to user confirming restart, then restarts the bot

        Outputs:
            Message to chat confirming that the bot is restarting.
        """

        await interaction.response.defer(ephemeral=True)
        if await confirmation(self.bot, interaction):
            await interaction.channel.send('Restarting...')
            await interaction.followup.send("The bot has restarted")
            os.execv(sys.argv[0], sys.argv)
        await interaction.followup.send("The bot was not restarted")

    @app_commands.command(description="shutdown the discord bot")
    @app_commands.default_permissions(administrator=True)
    async def stop(self, interaction:discord.Interaction):
        """Shutdown the discord bot
        Send message to user confirming shutdown. Exit program.

        Outputs:
            Message to user that discord bot is being shut down
        """

        await interaction.response.defer(ephemeral=True)
        if await confirmation(self.bot, interaction):
            await interaction.channel.send('Stopping...')
            await interaction.followup.send("Stopping the bot")
            await self.bot.close()
        await interaction.followup.send("The bot was not stopped")
