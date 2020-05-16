from datetime import datetime
from time import sleep

import discord
from discord.ext import commands


class ChannelManagment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role('cse-support')
    async def clear(self, ctx, amount=''):
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


def setup(bot):
    bot.add_cog(ChannelManagment(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
