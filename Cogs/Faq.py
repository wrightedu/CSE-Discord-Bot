from discord.ext import commands
from utils import *

async def setup(bot):
    await bot.add_cog(Faq(bot))


class Faq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.faq_channels = []

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listens to every message, responds if there is a '?' and the channel has been FAQ enabled
        """
        # If the author is a bot return
        if message.author.bot:
            return

        # Checks if the channel is a requested faq channel
        if message.channel in self.faq_channels:

            # If there is a ? in the content reply "That looks interesting" and break out of the loop
            if '?' in message.content:
                await message.reply("That looks interesting")
                # better response and @Wischgoll for advice
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def faq(self, ctx):
        """
        Allows/disallows the faq machine learning feature for a specific channel
        """
        # If the channel is in the list remove it and return
        if ctx.channel in self.faq_channels:
            self.faq_channels.remove(ctx.channel)
            await ctx.reply("FAQ has been disabled for this channel!")

            # Logging
            await log(self.bot, f'{ctx.author} has disabled FAQ for the {ctx.channel} channel')
            return
        
        # If the channel is not in the list add it to the end
        await ctx.reply("FAQ has been enabled for this channel!")
        self.faq_channels.append(ctx.channel)

        # Logging
        await log(self.bot, f'{ctx.author} has enabled FAQ for the {ctx.channel} channel')