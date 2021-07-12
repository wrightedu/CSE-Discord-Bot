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
        Take in the name of single cog from a user and reload it. Output a message confirming reload action 
        and use reload extension method on the cog. If reloading server managment, call load_server_managment
        method from CogManagment.py

        Args: 
            cog_name: Name of the cog that will be reloaded
        
        Outputs:
            Message to user informing them of what cog is being restarted. 

            """

        await ctx.send(f'Reloading {cog_name}')
        self.bot.reload_extension(f'Cogs.{cog_name}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, cog_name):
        """Unload a specific cog
        Take in the name of a cog from a user. If the user is not trying to unload the CogManagment cog,
        send a message confirming the action. Call unload_extension command from Discord.ext, passing in 
        the cog_name. 

        Args:
            cog_name: Name of the cog being unloaded

        Outputs:
            Message to user informing them of what cog is being unloaded.
            """

        if cog_name != 'CogManagement':
            await ctx.send(f'Unloading {cog_name}')
            self.bot.unload_extension(f'Cogs.{cog_name}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, cog_name):
        """Load a specific cog
        Take in the name of a cog from a user. Send a message confirming the action, and call load_extension 
        command from Discord.ext, passing in cog_name. If the cog is ServerManagment, call load_server_managment
        method from CogManagment.py

        Args: 
            cog_name: Name of the cog being loaded
        
        Outputs:
            Message to user informing them of what cog is being loaded.
        """

        await ctx.send(f'Loading {cog_name}')
        self.bot.load_extension(f'Cogs.{cog_name}')

    async def load_server_management(self):
        """Pass in information to the ServerManagment cog so it may handle role menus properly
        In the bots's presence, change the game to 'Building Servers' and the status to idle. Create empty 
        dictionaries for the reaction roles and reaction message ids. For every guild in the server, log that the 
        bot is doing work on said guild. Set the most likely filename for each server's reaction role as 
        reaction_roles_filename utilising the id of each guild for its respective reaction role file. If 
        said file exists, set a new key in reaction_roles as the guild id, and the item as the guild followed
        by the information from the reaction_roles file. When this has been done for all guilds, get the ServerManagment
        cog and pass in the reaction_roles and reaction_message_ids dictionaries. Set reaction_message_ids in the cog
        to the output of the create_roll_menu method from utils.py. The bot, guild, and reaction_roles dictionay
        are passed in to this method. 
        
        """
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
