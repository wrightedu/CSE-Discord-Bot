import datetime
from discord.ext import commands

from utils.utils import *

async def setup(bot:commands.Bot):
    """
    Setup function to initialize the Listeners cog.
    
    Parameters:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(Listeners(bot))


class Listeners(commands.Cog):
    """
    A class representing listeners for handling various events in the bot.

    Parameters:
        bot (commands.Bot): The bot instance.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        """Auto-reacts emojis to discord messages
        Any time anyone sends a message in #i-made-a-pr or #cs-help-room, the bot reacts with the poop emoji
        or the wave emoji respectively. The bot reacts to every message in the #i-made-a-pr channel, but only
        specific messages that are sent by TA's and contain specified keywords in the #cs-help-room channel.

        Outputs:
            An emoji reaction to a message that matches any necessary channel, author, and/or keyword criteria
        """

        # Checks if the channel is type of TextChannel to avoid errors from ephemeral messages
        if isinstance(ctx.channel, discord.TextChannel):
            if ctx.channel.name == 'i-made-a-pr' and ctx.author != self.bot.user:
                await ctx.add_reaction("💩")

            # Get the TA role from its name
            ta_role_name = 'Teaching Assistant'
            ta_role = discord.utils.get(ctx.guild.roles, name=ta_role_name)
            
            # Only react if its in the help room channel and if the user has the TA role
            if ctx.channel.name == 'cs-help-room' and ta_role in ctx.author.roles:
                # Establishes a list of keywords to check for in the message
                keywords = ['greetings', 'hi', 'hello', 'hey', 'howdy', 'yo', 'sup', 'office hours', 'help room', 'helproom', 'russ', 'joshi']
                message = ctx.content

                # Add the reaction if any keywords are found in the message
                if any(keyword in message.lower() for keyword in keywords):
                    await ctx.add_reaction("👋")


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Logs edited messages
        Will log any message that is edited and display both the original, and edited message in the message-log channel

        Args:
            before (discord.Message): The previous version of the message.
            after (discord.Message): The current version of the messsage.
        
        Outputs:
            A discord embed containing the original message, the editied message, who edited it, and when it was edited
        """

        # Checks if the channel is type of TextChannel to avoid errors from ephemeral messages
        if isinstance(before.channel, discord.TextChannel):
            # Get the channel to send the message to
            message_log_channel = discord.utils.get(before.guild.channels, name='message-log')

            # If the message log channel exists, and the message was not sent by the bot, log the message
            if message_log_channel and before.author != self.bot.user:
                # Create an embed to log the message
                embed = discord.Embed(title=f"Message Edited at [{str(datetime.datetime.now())[:-7]}]", color=0x00ff00)
                embed.add_field(name="Original Message", value=f'"{before.content}"', inline=False)
                embed.add_field(name="Edited Message", value=f'"{after.content}"', inline=False)
                embed.set_footer(text=f"Message edited by {after.author} in {before.channel.name}")

                # Send the embed to the message log channel
                await message_log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs deleted messages
        Will log any message that is deleted and display the original message in the message-log channel

        Args:
            message (discord.Message): The deleted message
        
        Outputs:
            A discord embed containing the deleted message, who deleted it, and when it was deleted
        """

        # Checks if the channel is type of TextChannel to avoid errors from ephemeral messages
        if isinstance(message.channel, discord.TextChannel):
            # Get the channel to send the message to
            message_log_channel = discord.utils.get(message.guild.channels, name='message-log')

            # If the message log channel exists, and the message was not sent by the bot, log the deleted message
            if message_log_channel and message.author != self.bot.user:
                # Create an embed to log the message
                embed = discord.Embed(title=f"Message Deleted at [{str(datetime.datetime.now())[:-7]}]", color=0xFF0000)
                embed.add_field(name="Message Deleted", value=f'"{message.content}"', inline=False)
                embed.set_footer(text=f"Message deleted by {message.author} in {message.channel.name}")

                # Send the embed to the message log channel
                await message_log_channel.send(embed=embed)
