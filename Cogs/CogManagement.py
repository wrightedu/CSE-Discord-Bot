import os
from os.path import exists, abspath

from typing import List
from enum import Enum

import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger


def get_cog_enums():
    """Dynamically create an enum of cog names from the cogs directory.

    Mostly to generate the list of cogs for the management of all cogs.
    Better than using autocomplete, which the user can still input custom
    values that don't exist, but using choices, they're restricted to the actual cogs.
    """
    list_of_cogs = {}

    for file in os.listdir("Cogs"):
        if not file.startswith("__") and file.endswith(".py"):
            cog_name = file[:-3]
            # if cog_name not in list_of_cogs:
            list_of_cogs[cog_name] = cog_name

    # if list_of_cogs == {}:
    # return

    global CogNames
    CogNames = Enum("CogNames", list_of_cogs)

    return list_of_cogs


# Initialize the CogNames enum before the CogManagement class is defined
# This ensures that the enum is available for use in the class methods
get_cog_enums()


async def setup(bot: commands.Bot):
    """
    Set up the CogManagement extension for the bot.

    Args:
        bot (commands.Bot): The instance of the bot.
    """
    await bot.add_cog(CogManagement(bot))


class CogManagement(commands.Cog):
    """CogManagement.

    A class to manage the loading, reloading, and unloading of cogs.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Load a specific cog")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def load(self, interaction: discord.Interaction, cog_name: CogNames):
        """Load a specific cog.

        Take in the name of a cog from a user. Send a message confirming the action, and call
        load_extension command from Discord.ext, passing in cog_name.

        Args:
            cog_name (CogNames): Name of the cog being loaded
                cog_name will be autofilled with all of the cogs we currently have
                and it will prevent the user from entering anything that is not a valid cog name

        Outputs:
            Message to user informing them of what cog is being loaded, and when the action is done.
        """
        cog_name = cog_name.value

        await interaction.response.send_message(f"Loading {cog_name}")

        # Attempt the load, if already loaded tell the user and return
        try:
            await self.bot.load_extension(f"Cogs.{cog_name}")
            await interaction.channel.send(f"Cog {cog_name} has been loaded")
            logger.success(f"{interaction.user} loaded the {cog_name} cog.")

        except commands.ExtensionAlreadyLoaded:
            await interaction.channel.send(f"Cog {cog_name} is already loaded")
            logger.warning(
                f"{interaction.user} attempted to load the {cog_name} cog, but it is already loaded."
            )

    @app_commands.command(description="Reload all cogs")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def reload_all(self, interaction: discord.Interaction):
        """Reload all cogs.

        Run /load_all. Send a message confirming the action, and call load_extension
        command from Discord.ext, passing in all cog names.

        Outputs:
            Message to user informing them of what cog is being loaded, and when the action is done.
        """
        await interaction.response.send_message("Reloading all cogs...")

        # Iterate through all loaded cogs and reload each one
        for cog in list(self.bot.extensions.keys()):
            try:
                await self.bot.reload_extension(cog)
                await interaction.channel.send(f"Cog {cog} has been reloaded")
                logger.success(f"{interaction.user} reloaded the {cog} cog.")

            except commands.ExtensionNotLoaded as _e:
                await interaction.channel.send(f"Cog {cog} is unloaded")
                logger.warning(
                    f"{interaction.user} attempted to reload the {cog} cog, but it is unloaded."
                )

            except commands.ExtensionNotFound as _e:
                await interaction.channel.send(f"Cog {cog} not found")
                logger.warning(
                    f"{interaction.user} attempted to reload the {cog} cog, but it was not found."
                )

        logger.success(f"{interaction.user} reloaded all cogs.")

    @app_commands.command(description="Reload a specific cog")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def reload(self, interaction: discord.Interaction, cog_name: CogNames):
        """Reload a specific cog.

        Take in the name of single cog from a user and reload it. Output a message confirming reload
        action and use reload extension method on the cog. If reloading server managment, call
        load_server_managment method from CogManagment.py

        Args:
            cog_name (CogNames): Name of the cog that will be reloaded
                cog_name will be autofilled with all of the cogs we currently have
                and it will prevent the user from entering anything that is not a valid cog name

        Outputs:
            Message to user informing them of what cog is being restarted, and when the action is
            done.
        """
        cog_name = cog_name.value

        # If the file exists it reloads the cog
        await interaction.response.send_message(f"Reloading {cog_name}")

        # Attempt the reload, if unloaded tell the user and return
        try:
            await self.bot.reload_extension(f"Cogs.{cog_name}")
            logger.success(f"{interaction.user} reloaded the {cog_name} cog.")

        except commands.ExtensionNotLoaded:
            await interaction.channel.send(f"Cog {cog_name} is unloaded")
            logger.warning(
                f"{interaction.user} attempted to reload the {cog_name} cog, but it is unloaded.",
            )
            return

        await interaction.channel.send(f"Cog {cog_name} has been reloaded")
        logger.success(f"{interaction.user} reloaded the {cog_name} cog.")

    @app_commands.command(description="Unload a specific cog")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def unload(self, interaction: discord.Interaction, cog_name: CogNames):
        """Unload a specific cog.

        Take in the name of a cog from a user. If the user is not trying to unload the CogManagment
        cog, send a message confirming the action. Call unload_extension command from Discord.ext,
        passing in the cog_name.

        Args:
            cog_name (CogNames): Name of the cog being unloaded
                `cog_name` will be autofilled with all of the cogs we currently have
                and it will prevent the user from entering anything that is not a valid cog name

        Outputs:
            Message to user informing them of what cog is being unloaded, and when the action is
            done.
        """
        cog_name = cog_name.value

        if cog_name != "CogManagement":
            await interaction.response.send_message(f"Unloading {cog_name}")

            # Attempt the unload, if already unloaded tell the user and return
            try:
                await self.bot.unload_extension(f"Cogs.{cog_name}")
                await interaction.channel.send(f"Cog {cog_name} has been unloaded")
                logger.success(f"{interaction.user} unloaded the {cog_name} cog.")

            except commands.ExtensionNotLoaded:
                await interaction.channel.send(f"Cog {cog_name} is already unloaded")
                logger.warning(
                    f"{interaction.user} attempted to unload the {cog_name} cog, but it is already unloaded."
                )

        else:
            await interaction.response.send_message(f"Cannot unload {cog_name}")

    @app_commands.command(name="sync", description="Syncs all slash commands")
    @app_commands.default_permissions(administrator=True)
    async def slash_sync(self, interaction: discord.Interaction):
        """Syncs all slash commands.

        Syncs application commands to the bot's global tree.
        Copies to current server.
        """

        await self.bot.tree.sync()  # syncs global tree to server/guilds
        await interaction.response.send_message("All slash commands have been synced")
        logger.success(
            f"{interaction.user} synced all slash commands in the {interaction.channel} channel",
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        """Syncs all slash commands.

        Syncs application commands to the bot's global tree.
        Copies to current server.
        """

        await self.bot.tree.sync()  # syncs global tree to server/guilds
        # needs to be run the first time a bot syncs to a server
        self.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.send("All slash commands have been synced")
        logger.success(
            f"{ctx.author} synced all slash commands in the {ctx.channel} channel",
        )
