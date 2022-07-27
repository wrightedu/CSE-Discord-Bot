from pathlib import Path
import pandas as pd

from discord.ext import commands
from utils import *

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
        """
        Listens to every message, responds if there is a '?' and the channel has been FAQ enabled
        """
        # If the author is a bot return
        if message.author.bot:
            return

        # Checks if the channel is a requested faq channel
        if message.channel.name in self.channel_names:

            # If there is a ? in the content reply "That looks interesting" and break out of the loop
            if '?' in message.content:
                faq_path = f"dummy-questions.csv"
                df = pd.read_csv(faq_path)
                questions = df["questions"].to_list()

                if message.content in questions:
                    answer = df.loc[df['questions'] == message.content,"answers"].values[0]

                await message.reply(f"Your question is as follows: '{message.content}'")
                await message.reply(answer)
                # better response and @Wischgoll for advice
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def faq(self, ctx):
        """
        Allows/disallows the faq machine learning feature for a specific channel
        """
        # If the channel is in the list remove it and return
        if ctx.channel.name in self.channel_names:
            self.channel_names.remove(ctx.channel.name)
            await ctx.reply("FAQ has been disabled for this channel!")

            # Logging
            await log(self.bot, f'{ctx.author} has disabled FAQ for the {ctx.channel} channel')
        
        # If the channel is not in the list add it to the end
        else:
            await ctx.reply("FAQ has been enabled for this channel!")
            self.channel_names.append(ctx.channel.name)

            # Logging
            await log(self.bot, f'{ctx.author} has enabled FAQ for the {ctx.channel} channel') 

        channels_path = r"assets/FAQ/channels.txt"
        path = Path(channels_path)
        with path.open('w') as f:
            for channel_name in self.channel_names:
                f.write(f"{channel_name}\n")
