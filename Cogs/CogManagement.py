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
        """Reload a specific cog
        Args: 
            cog_name: Name of the cog that will be reloaded

        Returns:
            """

        await ctx.send(f'Reloading {cog_name}')
        self.bot.reload_extension(f'Cogs.{cog_name}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, cog_name):
        """Unload a specific cog
        Args:
            cog_name: Name of the cog being unloaded

        Returns:
            """

        if cog_name != 'CogManagement':
            await ctx.send(f'Unloading {cog_name}')
            self.bot.unload_extension(f'Cogs.{cog_name}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, cog_name):
        """Load a specific cog
        Args: 
            cog_name: Name of the cog being loaded
        
        Returns:
        """

        await ctx.send(f'Loading {cog_name}')
        self.bot.load_extension(f'Cogs.{cog_name}')

    # TODO: Update command that git pulls and reloads all cogs
