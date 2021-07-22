import os
import sys
from time import sleep

from discord.ext import commands
from utils import *


def setup(bot):
    bot.add_cog(AdminCommands(bot))


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command(help='`-clear AMOUNT` to clear AMOUNT messages\n`-clear all` to clear all messages from this channel')
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=''):
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
            if not await confirmation(self.bot, ctx):
                return
            await ctx.send(f'Clearing all messages from this channel')
            await log(self.bot, f'{ctx.author} cleared {amount} messages from #{ctx.channel}')
            amount = 999999999999999999999999999999999999999999
        elif amount == '':
            await ctx.send(f'No args passed. Use `-clear AMOUNT` to clear AMOUNT messages. Use `-clear all` to clear all messages from this channel')
            await log(self.bot, f'{ctx.author} attempted to clear messages from #{ctx.channel}, but it failed because parameter "amount" was not passed')
            return
        else:
            amount = int(amount)
            if amount >= 10 and not await confirmation(self.bot, ctx):
                return
            await ctx.send(f'Clearing {amount} messages from this channel')
            await log(self.bot, f'{ctx.author} cleared {amount} messages from #{ctx.channel}')
        sleep(1)
        await ctx.channel.purge(limit=int(float(amount)) + 2)

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

        status = status.strip()
        if status.lower() == 'none':
            await self.bot.change_presence(activity=None)
            await log(self.bot, f'{ctx.author} disabled the custom status')
        elif len(status) <= 128:
            await self.bot.change_presence(activity=discord.Game(status))
            await log(self.bot, f'{ctx.author} changed the custom status to "Playing {status}"')

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
            exit(0)
