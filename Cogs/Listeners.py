from discord.ext import commands
from utils.utils import *


async def setup(bot):
    await bot.add_cog(Listeners(bot))


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        """Any time anyone sends a message in #i-made-a-pr, react with the poop emoji
        """
        if ctx.channel.name == 'i-made-a-pr' and ctx.author != self.bot.user:
            await ctx.add_reaction("💩")
