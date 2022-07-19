import os
import sys
from time import sleep
import re

from discord.ui import View, Button
from discord.ext import commands
from discord import MessageType
from utils import *


async def setup(bot):
    await bot.add_cog(Gourmet(bot))

class Gourmet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.normal_restaurant = []
        self.vegan_restaurant = []

    # Adding items to the normal_restaurant list
    def meat_add(self, rest_name):
        self.normal_restaurant.append(rest_name)

    # Menu that extends from a View
    class GourmetMenu(View):
        def __init__(self, *, cog, timeout=180):
            super().__init__(timeout=timeout)
            self.cog = cog
        
        # Not working yet
        @discord.ui.button(label="Meat",style=discord.ButtonStyle.blurple,emoji='\U0001F3B1')
        async def roll_M(self,interaction:discord.Interaction,button:discord.ui.Button):
            await interaction.response.edit_message(view=self)
        
        # Adds a restaurant to a list
        @discord.ui.button(label="Add Restaurant",style=discord.ButtonStyle.green)
        async def add(self,interaction:discord.Interaction,button:discord.ui.Button):

            # This must be here because of the user response
            # If the user response is before this it would show "interaction failed"
            # The interaction has not really failed however it hasnt happened quick enough.
            await interaction.response.send_message(f'Enter a restaurant to add to the list.')

            # Waiting for the user's response (with interactions!)
            msg = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)
            self.cog.normal_restaurant.append(msg.content)

        # Removes a restaurant from a list
        @discord.ui.button(label="Remove Restaurant",style=discord.ButtonStyle.red)
        async def delete(self,interaction:discord.Interaction,button:discord.ui.Button):

            # This must be here because of the user response
            # If the user response is before this it would show "interaction failed"
            # The interaction has not really failed however it hasnt happened quick enough.
            await interaction.response.send_message(content=f'Enter a restaurant to remove from the list.')

            # Waiting for the user's response (with interacitons!)
            msg = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # If the restaurant is not in the list it responds with an error
            if not msg.content in self.cog.normal_restaurant:
                await interaction.message.reply(content=f'Error: {msg.content} is not in the list.')
            else:
                self.cog.normal_restaurant.remove(msg.content)
        
        # Not working yet
        @discord.ui.button(label="Vegan",style=discord.ButtonStyle.blurple,emoji='\U0001F96C')
        async def roll_V(self,interaction:discord.Interaction,button:discord.ui.Button):
            await interaction.response.edit_message(view=self)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def feedMe(self, ctx):
        await ctx.send(view=self.GourmetMenu(cog=self))


