from datetime import datetime

import discord
from discord.ext import commands


class SupportTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ###### ================================== ######
    ######              Commands              ######
    ###### ================================== ######

    @commands.command()
    async def supportticket(self, ctx):
        await ctx.send(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @ them or email them at cse-support.wright.edu')


def setup(bot):
    bot.add_cog(SupportTickets(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
