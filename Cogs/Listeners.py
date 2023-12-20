from discord.ext import commands

from utils.utils import *


async def setup(bot:commands.Bot):
    await bot.add_cog(Listeners(bot))


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        """Any time anyone sends a message in #i-made-a-pr, react with the poop emoji"""

        # Checks if the channel is type of TextChannel to avoid errors from ephemeral messages
        if type(ctx.channel) == discord.TextChannel:
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