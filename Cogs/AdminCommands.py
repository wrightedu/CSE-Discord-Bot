import asyncio
import aiofiles
import os
import sys
from time import sleep
import re

import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger

from utils.utils import *


async def setup(bot: commands.Bot):
    """
    Setup function to initialize the AdminCommands cog.

    Parameters:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(AdminCommands(bot))


class AdminCommands(commands.Cog):
    """
    A class representing commands for administrative actions.

    Parameters:
        bot (commands.Bot): The bot instance.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        description="Sends an announcement to specified channels given by a select menu"
    )
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def announce(self, interaction: discord.Interaction):
        """
        Uses the bot to announce something instead of having an admin to do so.

        Outputs:
            The announcement to the specified channel(s) in the CSE server
            Logs that the specific user used the announcement command
        """
        await interaction.response.defer(ephemeral=True)

        class MultiChannelSelect(discord.ui.View):
            def __init__(self):
                super().__init__()  # Timeout after 60 seconds
                self.selected_channels = None

            @discord.ui.select(
                cls=discord.ui.ChannelSelect,
                placeholder="Select channels...",
                min_values=1,
                max_values=25,
                channel_types=[
                    discord.ChannelType.text,
                    discord.ChannelType.news,  # Wait until the user makes a selection or the view times out
                ],
            )
            async def callback(
                self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
            ):
                selected = (
                    select.values
                )  # This will be a list of discord.abc.GuildChannel objects
                channel_names = [channel.mention for channel in selected]

                await interaction.response.send_message(
                    content=(
                        f"You selected: {', '.join(channel_names)}\n"
                        "Please enter a message in this channel."
                    ),
                    ephemeral=True,
                )

                self.selected_channels = [await channel.fetch() for channel in selected]
                self.stop()  # Stop listening for more selections

        multi_channel_select = MultiChannelSelect()

        # Prompt the user to select channels
        await interaction.edit_original_response(
            content="Select the channels you want to announce in (Max: 25)",
            view=multi_channel_select,
        )

        # Wait until the user makes a selection or the view times out
        await multi_channel_select.wait()

        await interaction.delete_original_response()

        # Get the selected channels
        channels = multi_channel_select.selected_channels
        channel_names = [channel.mention for channel in channels]

        # Wait for the announcement message
        message = await self.bot.wait_for(
            "message",
            check=lambda message: message.author == interaction.user
            and message.channel == interaction.channel,
        )

        # Errors if the user tries to send a message over 2,000 characters (if they have nitro)
        if len(message.content) > 2000:
            await interaction.channel.send(
                "Just because you have nitro, doesn't mean I do! The `message` parameter can only take a message of 2000 characters or less."
            )

            logger.warning(
                f"{interaction.user} tried making an announcement from #{interaction.channel} but failed because the message was too long"
            )
            return

        # logs appropriately
        logger.success(
            f"{interaction.user} has executed the announcement command in #{interaction.channel}"
        )

        # sends the message to the specified channels
        for channel in channels:
            await channel.send(message.content)

        await interaction.response.send_message(
            f"Announcement sent to {', '.join(channel_names)}", ephemeral=True
        )

        # logs appropriately
        logger.success(
            f"{interaction.user} made an announcement from #{interaction.channel} to {', '.join(channel_names)}"
        )

    @app_commands.command(
        description="clears either 'all' or the specified number of messages from the channel"
    )
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def clear(self, interaction: discord.Interaction, amount: str):
        """Clears a specific number of messages from a guild
        Take in user input for the number of messages they would like to get cleared. If the amount is 'all',
        clear a very large number of messages from the server. Otherwise, send message confirming how many
        messages are being cleared and log it. Purge the appropriate number of messages from the channel.

        Args:
            amount (str): Number of messages to be removed

        Outputs:
            States the amount of messages being cleared or, if invalid input, help on how to use the command
        """

        await interaction.response.defer(ephemeral=True)
        if amount == "all":
            if not await confirmation(self.bot, interaction):
                await interaction.followup.send("Command not confirmed")
                return
            await interaction.channel.send("Clearing all messages from this channel")

            # Grabs orignal channel position
            original_position = interaction.channel.position

            # Copies channel and deletes all messages
            new_channel = await interaction.channel.clone(reason="Has been nuked")
            await interaction.channel.delete(reason="Nuked by admin command")
            logger.success(
                f"{interaction.user} cleared {amount} messages from #{interaction.channel}",
            )

            # Puts channel back in orignal position
            await new_channel.edit(position=original_position)

            # @'s user who ran the /clear command to the new channel created
            await new_channel.send(
                f"Cleared channel is ready: {interaction.user.mention}!"
            )

        else:
            try:
                amount = int(amount)
            except ValueError:
                await interaction.channel.send(
                    "The `amount` parameter can only take either `all` or a number."
                )

                logger.error(
                    f'{interaction.user} attempted to clear messages from #{interaction.channel}, but it failed because a valid "amount" was not passed'
                )

                await interaction.followup.send("`amount` parameter is invalid")

                return

            if amount < 10:
                await interaction.channel.send(
                    f"Clearing {amount} messages from this channel"
                )
                logger.success(
                    f"{interaction.user} cleared {amount} messages from #{interaction.channel}"
                )

                sleep(1)

                await interaction.channel.purge(limit=int(float(amount)) + 1)
                await interaction.followup.send(
                    f"Cleared {amount} messages from this channel"
                )
                return

            if amount >= 10 and not await confirmation(self.bot, interaction):
                await interaction.followup.send("Command not confirmed")
                return

            await interaction.channel.send(
                f"Clearing {amount} messages from this channel"
            )
            await interaction.channel.purge(limit=int(float(amount)) + 4)
            logger.success(
                f"{interaction.user} cleared {amount} messages from #{interaction.channel}"
            )

    @app_commands.command(
        description="removes a specified role from each member of a guild."
    )
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def clear_role(self, interaction: discord.Interaction, role: discord.Role):
        """Remove a role from each member of a guild.
        Remove the extra characters from the ID number of the guild obtained from the role_mention. Search through every
        memiber of a guild to see if they have the role that matches the ID in question. If the member has the role,
        remove it from their roles. Send message in chat confirming that the role has been removed, and the number of
        users it has been removed from.

        Args:
            role_mention (str): mention of role being removed

        Outputs:
            Message to chat regarding what role was removed and how many users were stripped of it
        """

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Removing role")
        guild = interaction.guild

        if role >= interaction.guild.me.top_role:
            await interaction.channel.send(
                f"I cannot remove the {role.mention} role from members because it is equal to or higher than my top role."
            )
            logger.warning(
                f"{interaction.user} tried clearing the '@{role.name}' role in #{interaction.channel} but failed because it is equal to or higher than the bot's top role",
            )
            return

        cleared_members = []

        logger.info(
            f"{interaction.user} is clearing the '@{role.name}' role from all members:",
        )

        async for member in guild.fetch_members():
            if role in member.roles:
                await member.remove_roles(role)
                name = member.nick if member.nick is not None else member.name

                logger.info(name)
                cleared_members.append(name)

        if len(cleared_members) > 10:
            await interaction.channel.send(
                f"Cleared {role.mention} from {len(cleared_members)} members"
            )
        elif len(cleared_members) == 0:
            await interaction.channel.send(f"No members have the role {role.mention}")
        else:
            await interaction.channel.send(
                f'Cleared {role.mention} from {", ".join(cleared_members)}'
            )

        logger.success(
            f"{interaction.user} cleared the '@{role.name}' role from {len(cleared_members)} members",
        )

    @app_commands.command(
        description="Extracts the tar archive that contains the corgi images"
    )
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def extract_corgis(self, interaction: discord.Interaction):
        """
        Extracts the tar archive that contains the corgi images
        Extracts the tar archive that contains the corgi images to the appropriate directory.
        If the extraction is successful, send a message to chat confirming it. If it fails, send an error message.

        Outputs:
            Message to chat confirming that the extraction was successful or an error message if it failed.
        """

        await interaction.response.defer(ephemeral=True)

        try:
            await extract_corgis(self.bot, interaction)
            await interaction.followup.send(
                "Corgi images extracted successfully", ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"An error occurred while extracting corgi images: {e}"
            )
            logger.error(
                f"{interaction.user} tried to extract corgi images in #{interaction.channel} but failed due to an error: {e}",
            )

    @app_commands.command(description="edit a specified message sent by the bot")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def edit_message(self, interaction: discord.Interaction, message_id: str):
        """
        Edit a specified message sent by the bot
        Take in user input for the message ID of the message they would like to edit. If the message is not found,
        it responds stating that the message could not be found. If the message is found, send a message
        to chat stating that the message has been edited and log it. Edit the message with the user's input.

        Args:
            message_id (str): ID of the message to be edited

        Outputs:
            States the message being edited or, if invalid input, help on how to use the command
        """

        await interaction.response.defer(ephemeral=True)

        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except discord.errors.NotFound:
            message = None

        if message is None:
            await interaction.followup.send(
                f"The message with the ID {message_id} could not be found. Make sure you are in same channel as the message you wish to edit."
            )

            logger.warning(
                f"{interaction.user} tried to edit the message with the ID `{message_id}` in #{interaction.channel} but failed because the message could not be found",
            )
            return

        if message.author != self.bot.user:
            await interaction.followup.send(
                f"The message with the ID {message_id} is not a message sent by the bot."
            )

            logger.warning(
                f"{interaction.user} tried to edit the message with the ID `{message_id}` in #{interaction.channel} but failed because it was not a message sent by the bot",
            )
            return

        bot_message = await interaction.followup.send(
            "Please enter the new message. Type 'cancel' to cancel."
        )

        try:
            new_message = await self.bot.wait_for(
                "message",
                check=lambda message: message.author == interaction.user,
                timeout=60.0,
            )

            if new_message.content == "cancel":
                await bot_message.edit(content="Message edit cancelled")
                await new_message.delete()

                logger.warning(
                    f"{interaction.user} cancelled the edit of the message in #{interaction.channel}",
                )

            else:
                await message.edit(content=new_message.content)
                await new_message.delete()

                logger.success(
                    f"{interaction.user} edited the message with the ID `{message_id}` in #{interaction.channel}",
                )
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "You took too long to respond. Exiting command..."
            )
            return

    @app_commands.command(description="set status of discord bot")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def status(self, interaction: discord.Interaction, status: str):
        """Set status of discord bot
        Take in a user input for the status of the Discord Bot. If the status is 'none', log that the user
        removed the custom status. Otherwise, ensure proper length of message, and calls change_presence method
        on the discord bot and passes in the user input to the method. Log the author and new status.

        Args:
            status (str): Text to be displayed
        """

        await interaction.response.defer(ephemeral=True)

        # open a file to store the status in
        async with aiofiles.open("status.txt", mode="w") as f:

            status = status.strip()
            if status.lower() == "none":
                await self.bot.change_presence(activity=None)

                logger.success(f"{interaction.user} disabled the custom status")
                await f.write("Raider Up!")  # Default status for when the bot restarts

            elif len(status) <= 128:
                await self.bot.change_presence(activity=discord.Game(status))

                logger.success(
                    f'{interaction.user} changed the custom status to "Playing {status}"',
                )
                await f.write(status)  # write the new status to the file

            elif len(status) > 128:
                await interaction.followup.send(
                    "Unable to set status, length of given status is > 128"
                )
                return  # returns so the interaction doesn't set a followup twice
        await interaction.followup.send("Status set")

    @app_commands.command(description="outputs various stats of the server")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def stats(self, interaction: discord.Interaction):
        """Outputs various stats of the server
        Send message with server stats to user

        Outputs:
            Message to chat including total number of channels, text channels, voice channels, users, classes, roles,
            and people with top ten roles.
        """

        guild = interaction.guild

        embed = discord.Embed(
            title="Server Stats",
            description="Important Stats of the Server",
            color=discord.Color.green(),
        )

        total_text_channels = len(guild.text_channels)
        total_voice_channels = len(guild.voice_channels)
        total_channels = total_text_channels + total_voice_channels
        total_users = len(interaction.guild.members)

        num_roles = 0
        for role in guild.roles:
            num_roles += 1

        num_classes = 0
        for category in guild.categories:
            class_name = re.search(r"^\w{2,3} \d{4}", category.name)
            if class_name is not None:
                num_classes += 1

        embed.add_field(name="Total Channels: ", value=total_channels)
        embed.add_field(name="Text Channels: ", value=total_text_channels)
        embed.add_field(name="Voice Channels: ", value=total_voice_channels)
        embed.add_field(name="Max Channels: ", value=500)
        embed.add_field(name="Total Users: ", value=total_users)
        embed.add_field(name="Total Classes: ", value=num_classes)
        embed.add_field(name="Total Roles: ", value=num_roles)
        embed.add_field(name=chr(173), value=chr(173))
        embed.add_field(name=chr(173), value=chr(173))
        embed.add_field(name="Users with\nTop Roles", value="\u200b")
        embed.add_field(name=chr(173), value=chr(173))
        embed.add_field(name=chr(173), value=chr(173))

        roles_list = []
        for role in guild.roles:
            users_with_role = len(role.members)
            roles_list.append((role, users_with_role))

        top_roles = sorted(roles_list, key=lambda y: y[1], reverse=True)[1:]

        for index, value in enumerate(top_roles):
            if index > 9:
                break
            embed.add_field(name=value[0], value=value[1])

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="restart the discord bot")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def restart(self, interaction: discord.Interaction):
        """Restart the discord bot
        Send message to user confirming restart, then restarts the bot

        Outputs:
            Message to chat confirming that the bot is restarting.
        """

        await interaction.response.defer(ephemeral=True)
        if await confirmation(self.bot, interaction):
            await interaction.channel.send("Restarting...")
            await interaction.followup.send("The bot has restarted")
            os.execv(sys.argv[0], sys.argv)
        await interaction.followup.send("The bot was not restarted")

    @app_commands.command(description="shutdown the discord bot")
    @app_commands.default_permissions(administrator=True)
    @logger.catch
    async def stop(self, interaction: discord.Interaction):
        """Shutdown the discord bot
        Send message to user confirming shutdown. Exit program.

        Outputs:
            Message to user that discord bot is being shut down
        """

        await interaction.response.defer(ephemeral=True)
        if await confirmation(self.bot, interaction):
            await interaction.channel.send("Stopping...")
            await interaction.followup.send("Stopping the bot")
            await self.bot.close()
        await interaction.followup.send("The bot was not stopped")
