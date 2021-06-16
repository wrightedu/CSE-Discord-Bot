import json
from os.path import exists

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
        if cog_name == 'ServerManagement':
            await self.load_server_management()

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
        if cog_name == 'ServerManagement':
            await self.load_server_management()

    async def load_server_management(self):
        # Initialize each guild
        await self.bot.change_presence(activity=discord.Game(f'Building servers'), status=discord.Status.idle)
        reaction_roles = {}
        reaction_message_ids = []
        for guild in self.bot.guilds:
            await log(self.bot, f'Initializing server: {guild}')

            # Load reaction roles JSONs
            reaction_roles_filename = f'reaction_roles_{guild.id}.json'

            # Load reaction roles from file
            if exists(reaction_roles_filename):
                with open(reaction_roles_filename, 'r') as f:
                    reaction_roles[guild.id] = (guild, json.loads(f.read()))

        # Load reaction roles into ServerManagement cog
        cog = self.bot.get_cog('ServerManagement')
        cog.reaction_roles = reaction_roles
        cog.reaction_message_ids = reaction_message_ids

        # Generate role menu
        try:
            cog.reaction_message_ids = await create_role_menu(self.bot, guild, reaction_roles)
        except Exception:
            await log(self.bot, f'    failed, no reaction roles JSON')

    # TODO: Update command that git pulls and reloads all cogs
