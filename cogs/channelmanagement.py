from datetime import datetime

import discord
from discord.ext import commands


class ChannelManagment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role('cse-support')
    async def clear(self, ctx, amount):
        if amount.lower() == 'all':
            amount = 99999999999999999999999


def setup(bot):
    bot.add_cog(ChannelManagment(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
