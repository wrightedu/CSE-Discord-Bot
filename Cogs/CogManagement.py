from discord.ext import commands
from utils import *


def setup(bot):
    bot.add_cog(CogManagement(bot))


class CogManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, cog_name):
        await ctx.send(f'Reloading {cog_name}')
        self.bot.reload_extension(f'Cogs.{cog_name}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, cog_name):
        if cog_name != 'CogManagement':
            await ctx.send(f'Unloading {cog_name}')
            self.bot.unload_extension(f'Cogs.{cog_name}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, cog_name):
        await ctx.send(f'Loading {cog_name}')
        self.bot.load_extension(f'Cogs.{cog_name}')

    # TODO: Update command that git pulls and reloads all cogs
