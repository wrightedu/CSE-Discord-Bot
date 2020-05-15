from datetime import datetime

import discord
from discord.ext import commands


class CogControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ###### ================================== ######
    ######              Commands              ######
    ###### ================================== ######

    @commands.command()
    @commands.has_role('cse-support')
    async def load(self, ctx, cog):
        cog = cog.lower()
        if cog != 'cogcontrol':
            self.bot.load_extension(f'cogs.{cog}')
            await ctx.send(f'Loaded cog: {cog}')
            await log(f'Loaded cog: {cog}')
        else:
            await ctx.send(f'Cog {cog} is permanently loaded')

    @commands.command()
    @commands.has_role('cse-support')
    async def unload(self, ctx, cog):
        cog = cog.lower()
        if cog != 'cogcontrol':
            self.bot.unload_extension(f'cogs.{cog}')
            await ctx.send(f'Unloaded cog: {cog}')
            await log(f'Unloaded cog: {cog}')
        else:
            await ctx.send(f'Cog {cog} cannot be unloaded')

    @commands.command()
    @commands.has_role('cse-support')
    async def reload(self, ctx, cog):
        cog = cog.lower()
        if cog != 'cogcontrol':
            try:
                self.bot.unload_extension(f'cogs.{cog}')
            except Exception:
                pass
            self.bot.load_extension(f'cogs.{cog}')
            await ctx.send(f'Reloaded cog: {cog}')
            await log(f'Reloaded cog: {cog}')
        else:
            await ctx.send(f'Cog {cog} cannot be reloaded')


def setup(bot):
    bot.add_cog(CogControl(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
