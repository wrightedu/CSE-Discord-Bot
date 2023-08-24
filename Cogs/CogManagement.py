import os
from os.path import exists, abspath

from discord.ext import commands
from discord import app_commands
from typing import List

from utils.utils import *


def get_choices():
    """Gets cog names
    Reads all cog names and adds them to a list. This list is returned and added to a list of choices for 
    autocomplete

    Outputs:
        List of cog names
    """

    cogs_list = []
    for file in os.listdir('Cogs'):
        if not file.startswith('__') and file.endswith('.py'):
            cogs_list.append(f'{file[:-3]}')
    return cogs_list

async def setup(bot:commands.Bot):
    choices = get_choices()
    await bot.add_cog(CogManagement(bot, choices))


class CogManagement(commands.Cog):
    def __init__(self, bot, choices):
        self.bot = bot
        self.choices = choices

    @app_commands.command(description="Load a specific cog")
    @app_commands.default_permissions(administrator=True)
    async def load(self, interaction:discord.Interaction, cog_name:str):
        """Load a specific cog
        Take in the name of a cog from a user. Send a message confirming the action, and call load_extension
        command from Discord.ext, passing in cog_name. If the cog is ServerManagment, call load_server_managment
        method from CogManagment.py

        Args:
            cog_name (str): Name of the cog being loaded
                cog_name will be autofilled with all of the cogs we currently have

        Outputs:
            Message to user informing them of what cog is being loaded, and when the action is done.
        """

        file = abspath('Cogs/' + cog_name + '.py')

        # If the file exists it loads the cog
        if exists(file):
            await interaction.response.send_message(f'Loading {cog_name}')

            # Attempt the load, if already loaded tell the user and return
            try:
                await self.bot.load_extension(f'Cogs.{cog_name}')
            except:
                await interaction.channel.send(f'Cog {cog_name} is already loaded')
                return
            await interaction.channel.send(f'Cog {cog_name} has been loaded')
            await log(self.bot, f'{interaction.user} loaded the {cog_name} cog.')
        else:
            await interaction.response.send_message(f'Cog {cog_name} does not exist. Please be sure you spelled it correctly.')
            await log(self.bot, f'{interaction.user} attempted to reload the {cog_name} cog, but failed.')

    @app_commands.command(description="Reload a specific cog")
    @app_commands.default_permissions(administrator=True)
    async def reload(self, interaction:discord.Interaction, cog_name:str):
        """Reload a specific cog
        Take in the name of single cog from a user and reload it. Output a message confirming reload action
        and use reload extension method on the cog. If reloading server managment, call load_server_managment
        method from CogManagment.py

        Args:
            cog_name (str): Name of the cog that will be reloaded
                cog_name will be autofilled with all of the cogs we currently have

        Outputs:
            Message to user informing them of what cog is being restarted, and when the action is done.
        """

        file = abspath('Cogs/' + cog_name + '.py')

        # If the file exists it reloads the cog
        if exists(file):
            await interaction.response.send_message(f'Reloading {cog_name}')

            # Attempt the reload, if unloaded tell the user and return
            try:
                await self.bot.reload_extension(f'Cogs.{cog_name}')
            except:
                await interaction.channel.send(f'Cog {cog_name} is unloaded')
                return
            await interaction.channel.send(f'Cog {cog_name} has been reloaded')
            await log(self.bot, f'{interaction.user} reloaded the {cog_name} cog.')
        else:
            await interaction.response.send_message(f'Cog {cog_name} does not exist. Please be sure you spelled it correctly.')
            await log(self.bot, f'{interaction.user} attempted to reload the {cog_name} cog, but failed.')

    @app_commands.command(description="Unload a specific cog")
    @app_commands.default_permissions(administrator=True)
    async def unload(self, interaction:discord.Interaction, cog_name:str):
        """Unload a specific cog
        Take in the name of a cog from a user. If the user is not trying to unload the CogManagment cog,
        send a message confirming the action. Call unload_extension command from Discord.ext, passing in
        the cog_name.

        Args:
            cog_name (str): Name of the cog being unloaded
                cog_name will be autofilled with all of the cogs we currently have

        Outputs:
            Message to user informing them of what cog is being unloaded, and when the action is done.
        """

        file = abspath('Cogs/' + cog_name + '.py')

        # If the file exists it unloads the cog
        if exists(file):
            if cog_name != 'CogManagement':
                await interaction.response.send_message(f'Unloading {cog_name}')

                # Attempt the unload, if already unloaded tell the user and return
                try:
                    await self.bot.unload_extension(f'Cogs.{cog_name}')
                except:
                    await interaction.channel.send(f'Cog {cog_name} is already unloaded')
                    return
                await interaction.channel.send(f'Cog {cog_name} has been unloaded')
                await log(self.bot, f'{interaction.user} unloaded the {cog_name} cog.')
            else:
                await interaction.response.send_message(f'Cannot unload {cog_name}')
                return
        else:
            await interaction.response.send_message(f'Cog {cog_name} does not exist. Please be sure you spelled it correctly.')
            await log(self.bot, f'{interaction.user} attempted to unload the {cog_name} cog, but failed.')

    # Autocomplete functionality for the parameter "cog_name" in the load, reload, and unload commands
    @load.autocomplete("cog_name")
    @reload.autocomplete("cog_name")
    @unload.autocomplete("cog_name")
    async def cog_auto(self, interaction:discord.Interaction, current:str) -> List[app_commands.Choice[str]]:
        data = []
        # For every choice if the typed in value is in the choice add it to the possible options
        for choice in self.choices:
            if current.lower() in choice.lower():
                data.append(app_commands.Choice(name=choice, value=choice))
        return data

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        """Syncs all slash commands
        Syncs application commands to the bot's global tree.
        Copies to current server.
        """

        await self.bot.tree.sync()      # syncs global tree to server/guilds
        self.bot.tree.copy_global_to(guild=ctx.guild)       # needs to be run the first time a bot syncs to a server
        await ctx.send(f'All slash commands have been synced')
        await log(self.bot, f'{ctx.author} synced all slash commands in the {ctx.channel} channel')
