import asyncio
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
        await log(self.bot, f"{interaction.user} has executed the announcement command in the {interaction.channel}")

        # gets the channel ids from the mentions
        channel_ids = channel_mentions.split()
        channels = []
        for channel_id in channel_ids:
            channel_id = channel_id.replace('<#', '')
            channel_id = channel_id.replace('>', '')

            # ensures the channel mentions can be converted to integers
            try:
                int(channel_id)
            except ValueError:
                await interaction.channel.send("The `channel_mentions` parameter can only take channel mentions (i.e. of format `#channel`).")
                await log(self.bot, f"{interaction.user} tried making an announcement from #{interaction.channel} but failed of invalid channel mention(s).")
                return

            # ensures the channels exist
            channel = self.bot.get_channel(int(channel_id))
            if (channel == None):
                await interaction.channel.send(f"Channel with id '{channel_id}' could not be found. The `channel_mentions` parameter can only take channel mentions (i.e. of format `#channel`).")
                await log(self.bot, f"{interaction.user} tried making an announcement from #{interaction.channel} but failed of invalid channel mention(s).")
                return
            channels.append(channel)

        # sends the message to the specified channels
        for channel in channels:
            await channel.send(message.content)
        
        # logs appropriately
        await log(self.bot, f"{interaction.user} made an announcement from #{interaction.channel} to the {channels} channels")


    @app_commands.command(description="clears either 'all' or the specified number of messages from the channel")
    @app_commands.default_permissions(administrator=True)
    async def clear(self, interaction:discord.Interaction, amount:str):
        """Clears a specific number of messages from a guild
        Take in user input for the number of messages they would like to get cleared. If the amount is 'all',
        clear a very large number of messages from the server. If the amount is blank, tell user how to more
        properly use the command. Otherwise, send message confirming how many messages are being cleared and log it.
        Purge the appropriate number of messages from the channel.

        Args:
            amount (str): Number of messages to be removed

        Outputs:
            States the amount of messages being cleared or, if invalid input, help on how to use the command
        """

        if amount == 'all':
            if not await confirmation(self.bot, interaction):
                return
            await interaction.channel.send(f'Clearing all messages from this channel')
            await log(self.bot, f'{interaction.user} cleared {amount} messages from #{interaction.channel}')
            amount = 999999999999999999999999999999999999999999

        else:
            try:
                amount = int(amount)
            except ValueError:
                await interaction.response.send_message("The `amount` parameter can only take either `all` or a number.")
                await log(self.bot, f'{interaction.user} attempted to clear messages from #{interaction.channel}, but it failed because a valid "amount" was not passed')
                return

            if amount >= 10 and not await confirmation(self.bot, interaction): # deletes 3 fewer messages if going into confirmation for some reason
                return
            await interaction.channel.send(f'Clearing {amount} messages from this channel')
            await log(self.bot, f'{interaction.user} cleared {amount} messages from #{interaction.channel}')

        sleep(1)
        await interaction.channel.purge(limit=int(float(amount)) + 1)

    # @commands.command(help='`-clear AMOUNT` to clear AMOUNT messages\n`-clear all` to clear all messages from this channel')
    # @commands.has_permissions(administrator=True)
    # async def clear(self, ctx, amount=''):
    #     """Clears a specific number of messages from a guild
    #     Take in user input for the number of messages they would like to get cleared. If the amount is 'all',
    #     clear a very large number of messages from the server. If the amount is blank, tell user how to more
    #     properly use the command. Otherwise, send message confirming how many messages are being cleared and log it.
    #     Purge the appropriate number of messages from the channel.

    #     Args:
    #         amount (str): Number of messages to be removed

    #     Outputs:
    #         States the amount of messages being cleared or, if invalid input, help on how to use the command
    #     """

    #     if amount == 'all':
    #         if not await confirmation(self.bot, ctx):
    #             return
    #         await ctx.send(f'Clearing all messages from this channel')
    #         await log(self.bot, f'{ctx.author} cleared {amount} messages from #{ctx.channel}')
    #         amount = 999999999999999999999999999999999999999999
    #     elif amount == '':
    #         await ctx.send(f'No args passed. Use `-clear AMOUNT` to clear AMOUNT messages. Use `-clear all` to clear all messages from this channel')
    #         await log(self.bot, f'{ctx.author} attempted to clear messages from #{ctx.channel}, but it failed because parameter "amount" was not passed')
    #         return
    #     else:
    #         amount = int(amount)
    #         if amount >= 10 and not await confirmation(self.bot, ctx):
    #             return
    #         await ctx.send(f'Clearing {amount} messages from this channel')
    #         await log(self.bot, f'{ctx.author} cleared {amount} messages from #{ctx.channel}')
    #     sleep(1)
    #     await ctx.channel.purge(limit=int(float(amount)) + 2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearrole(self, ctx, *, role_id):
        """Remove a role from each member of a guild.
        Remove the extra characters from the ID number of the guild. Search through every member of a guild to see if
        they have the role that matches the ID in question. If the member has the role, remove it from their roles. Send
        message in chat confirming that the role has been removed, and the number of users it has been removed from.

        Args:
            role_id (str): ID of the role being removed

        Outputs:
            Message to chat regarding what role was removed and how many users were stripped of it
        """

        guild = ctx.guild
        role = discord.utils.get(guild.roles, id=int(role_id[3:-1]))

        cleared_members = []

        await log(self.bot, f'{ctx.author} is clearing {role} from all members:')
        # for member in role.get_all_members():
        async for member in ctx.guild.fetch_members():
            if role in member.roles:
                await member.remove_roles(role)
                name = member.nick if member.nick is not None else member.name
                await log(self.bot, name, False)
                cleared_members.append(name)

        if len(cleared_members) > 10:
            await ctx.send(f'Cleared @{role} from {len(cleared_members)} members')
        elif len(cleared_members) == 0:
            await ctx.send(f'No members have the role @{role}')
        else:
            await ctx.send(f'Cleared @{role} from {", ".join(cleared_members)}')
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def downloadcorgis(self, ctx, amount):
        """Downloads a given number of corgi pictures.
        Convert user input to an integer. If this is not possible, set the amount of pictures as 100.
        Call the download_corgies method from utils.py. Log the user and number of images downloaded.

        Args:
            amount (int): Number of pictures/pieces of media being downloaded

        Outputs:
            Message to log stating the user that executed the command and how many images were downloaded
            Message to user if the input was invalid. States that 100 corgis are downloaded.
        """

        try:
            amount = int(amount)
        except Exception:
            amount = 100
            await ctx.send(f'Invalid parameter, downloading {amount} images')
        await download_corgis(self.bot, ctx, amount)
        await log(self.bot, f'{ctx.author} ran /downloadcorgis {amount} in #{ctx.channel}')
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def history(self, ctx):
        """Outputs all messages from a specified user after a specified date with some metadata to a file
        Prompts user for username and date. Outputs messages authored by that username and sent after that date
        to a file. Outputs file to discord channel if it is less that 4 MB.

        Outputs:
            A file to chat including all messages from a user after a date, whether those messages are a reply,
            a link to those messages, and all reactions to those messages.
        """

        guild = ctx.guild

        await ctx.send(f"Please enter a user's discord username.")
        username_message = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author)

        member_found = False
        for member in guild.members:
            if member.name == username_message.content:
                member_found = True
                break

        if not member_found:
            await ctx.send(f"That user is no longer active in the server. Would you like to continue this search query anyway?")
            if not await confirmation(self.bot, ctx, confirm_string="yes"):
                return
        that_day = months_ago(4)
        
        history_file = open("/tmp/history.txt", "w")
        channel = ctx.channel
        # gets 250 most recent messages posted less than 4 months ago
        messages = [message async for message in channel.history(limit=250, after=that_day, oldest_first=False)]

        for message in messages:
            if message.author.name == username_message.content and message.type is MessageType.default:
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
            await ctx.send(f"No messages were found.")
        elif size <= 4194304:
            await ctx.send(file=discord.File("/tmp/history.txt"))
        else:
            await ctx.send(f"Error: The file is greater than 4 MB and will therefore not be output.")

        os.remove("/tmp/history.txt")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, *, status):
        """Set status of discord bot
        Take in a user input for the status of the Discord Bot. If the status is 'none', log that the user
        removed the custom status. Otherwise, ensure proper length of message, and calls change_presence method
        on the discord bot and passes in the user input to the method. Log the author and new status.

        Args:
            status (str): Text to be displayed
        """

        # open a file to store the status in
        async with aiofiles.open('status.txt', mode='w') as f:
        
            status = status.strip()
            if status.lower() == 'none':
                await self.bot.change_presence(activity=None)
                await log(self.bot, f'{ctx.author} disabled the custom status')
                await f.write('Raider Up!') # Default status for when the bot restarts
            elif len(status) <= 128:
                await self.bot.change_presence(activity=discord.Game(status))
                await log(self.bot, f'{ctx.author} changed the custom status to "Playing {status}"')
                await f.write(status) # write the new status to the file
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stats(self, ctx):
        """Outputs various stats of the server
        Send message with server stats to user

        Outputs:
            Message to chat including total number of channels, text channels, voice channels, users, classes, roles,
            and people with top ten roles.
        """

        guild = ctx.guild

        embed = discord.Embed(
            title="Server Stats",
            description="Important Stats of the Server",
            color=discord.Color.green())

        total_text_channels = len(guild.text_channels)
        total_voice_channels = len(guild.voice_channels)
        total_channels = total_text_channels + total_voice_channels 
        total_users = len(ctx.guild.members)

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

        await ctx.reply(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restart(self, ctx):
        """Restart the discord bot
        Send message to user confirming restart, then restarts the bot

        Outputs:
            Message to chat confirming that the bot is restarting.
        """

        if await confirmation(self.bot, ctx):
            await ctx.send('Restarting...')
            os.execv(sys.argv[0], sys.argv)

    @commands.command(aliases=['shutdown', 'poweroff', 'exit'])
    @commands.has_permissions(administrator=True)
    async def stop(self, ctx):
        """Shutdown the discord bot
        Send message to user confirming shutdown. Exit program.

        Outputs:
            Message to user that discord bot is being shut down
        """

        if await confirmation(self.bot, ctx):
            await ctx.send('Stopping...')
            await ctx.bot.close()
