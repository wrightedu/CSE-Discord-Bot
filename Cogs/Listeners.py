from discord.ext import commands
from utils import *


def setup(bot):
    bot.add_cog(Listeners(bot))


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        channel = message.channel
        if channel.name == 'i-made-a-poopy':
            await message.add_reaction("💩")
