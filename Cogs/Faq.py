from pathlib import Path
import pandas as pd

from discord.ext import commands
from discord import app_commands

from utils.utils import *


async def setup(bot):
    channels_path = r"assets/FAQ/channels.txt"
    path = Path(channels_path)
    channel_names = []
    
    # if file exists, appends channel names to a list for use with faq command
    if path.is_file():
        with path.open() as f:
            for channel_name in f:
                channel_name = channel_name.strip()
                channel_names.append(channel_name)
    # initialize cog with no file
    else:
        print("Channels file for faq command does not exist.")
    
    await bot.add_cog(Faq(bot, channel_names))


class Faq(commands.Cog):
    def __init__(self, bot, channel_names):
        self.bot = bot
        self.channel_names = channel_names

    @commands.Cog.listener()
    async def on_message(self, message):
        """Responds to messages with `?` in them
        Listens to messages in faq-enabled channels.
        If a `?` is present, responds with the user's original question.
        Responds with the sample question and appropriate answer if a keyword is detected as well.
        """

        if message.author.bot:
            return
        
        if message.channel.type == discord.ChannelType.private:
            return

        if message.channel.name in self.channel_names:
            if '?' in message.content:
                faq_path = r"assets/FAQ/sample-FAQ.csv"
                df = pd.read_csv(faq_path)
                keywords = df["keywords"].to_list()
                message.content = message.content.replace("?", "")

                await message.reply(f"Your question is as follows: '{message.content}'")

                if message.content in keywords:
                    question = df.loc[df['keywords'] == message.content,"questions"].values[0]
                    answer = df.loc[df['keywords'] == message.content,"answers"].values[0]
                    await message.reply(question)
                    await message.reply(answer)

    @app_commands.command(description="Enable bot monitoring of a channel")
    @app_commands.default_permissions(administrator=True)
    async def faq(self, interaction:discord.Interaction):
        """Enables or disables bot monitoring of a channel
        Adds or removes channel in which command is run to a list
        Overwrites channels file with contents of list for persistent use
        """

        # If the channel is in the list remove it and return
        if interaction.channel.name in self.channel_names:
            self.channel_names.remove(interaction.channel.name)
            await interaction.response.send_message("FAQ has been disabled for this channel!")

            # Logging
            await log(self.bot, f'{interaction.user} has disabled FAQ for the {interaction.channel} channel')
        
        # If the channel is not in the list add it to the end
        else:
            await interaction.response.send_message("FAQ has been enabled for this channel!")
            self.channel_names.append(interaction.channel.name)

            # Logging
            await log(self.bot, f'{interaction.user} has enabled FAQ for the {interaction.channel} channel') 

        channels_path = r"assets/FAQ/channels.txt"
        path = Path(channels_path)
        with path.open('w') as f:
            for channel_name in self.channel_names:
                f.write(f"{channel_name}\n")
