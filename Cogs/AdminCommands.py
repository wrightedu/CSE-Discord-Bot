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
        if await confirmation(self.bot, ctx):
            await ctx.send('Restarting...')
            os.execv(sys.argv[0], sys.argv)

    @commands.command(aliases=['shutdown', 'poweroff', 'exit'])
    @commands.has_permissions(administrator=True)
    async def stop(self, ctx):
        if await confirmation(self.bot, ctx):
            await ctx.send('Stopping...')
            exit(0)
