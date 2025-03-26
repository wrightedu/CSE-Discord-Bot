import random
import copy
import pandas as pd
import re

from discord.ui import View
from discord.ext import commands
from discord import app_commands


from utils.utils import *


async def setup(bot):
    await bot.add_cog(Gourmet(bot))
    

class Gourmet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        csv_filepath = "assets/restaurants.csv"
        self.restaurants = pd.read_csv(csv_filepath)


    # Menu that extends from a View
    class GourmetMenu(View):
        def __init__(self, *, cog, timeout=180):
            super().__init__(timeout=timeout)
            self.cog = cog
            self.restaurants = copy.deepcopy(cog.restaurants).sample(frac=1).reset_index(drop=True)

        @discord.ui.button(label="Random", style=discord.ButtonStyle.blurple, emoji='\U0001F3B1')
        async def random(self, interaction:discord.Interaction, button:discord.ui.Button):
            """Returns a random restaurant"""

            if not len(self.restaurants) == 0:
                restaurant = self.restaurants.head(1)
                self.restaurants = self.restaurants.drop(restaurant.index)

                await interaction.response.edit_message(content='**' + restaurant.iloc[0]['name'] + '**', view=self)
            else:
                await interaction.response.edit_message(content='**__You have run out of restaurants. You are going to Arby\'s.__**', view=self)
        
        @discord.ui.button(label="Add Restaurant", style=discord.ButtonStyle.green)
        async def add(self, interaction:discord.Interaction, button:discord.ui.Button):
            """Adds a restaurant
            Asks user to enter a restaurant name
            Adds the name to the list of restaurants if not already there
            """

            # If the user response is before this, it would show "interaction failed"
            # The interaction has not really failed; however, it hasnt happened quickly enough.
            await interaction.response.edit_message(content='**__Enter a restaurant to add to the list.__**', view=self)

            # Waiting for the user's response (with interactions!)
            msg = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # Check if restaurant is already in list
            if len(self.cog.restaurants[self.cog.restaurants['name'] == msg.content]) > 0:
                await interaction.message.edit(content=f'**__Error: {msg.content} already is in the restaurant list.__**', view=self)
                return

            # Create new row
            resturant = pd.DataFrame({'name': [msg.content]})

            # Append new restaurant into restaurants
            self.cog.restaurants = pd.concat([self.cog.restaurants, resturant], ignore_index=True)

            # Append new restaurants into current list of restuarants
            self.restaurants = pd.concat([self.restaurants, resturant], ignore_index=True)

            # Write restaurants into csv
            await self.cog.write_restaurants()

            # Return added
            await interaction.message.edit(content=f'**__{msg.content} has been added to the list.__**')

        @discord.ui.button(label="Remove Restaurant", style=discord.ButtonStyle.red)
        async def remove(self, interaction:discord.Interaction, button:discord.ui.Button):
            """Removes a restaurant
            Asks user to enter a restaurant name
            Removes the name from the list of restaurants if already there
            """

            # If the user response is before this it would show "interaction failed"
            # The interaction has not really failed however it hasnt happened quick enough.
            await interaction.response.edit_message(content=f'**__Enter a restaurant to remove from the list.__**', view=self)

            # Waiting for the user's response (with interactons!)
            msg = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # Turning msg to lowercase
            msg.content = msg.content.casefold()

            # If the restaurant is not in the list it responds with an error
            for rest in self.main_list:
                if msg.content == rest.casefold():
                    self.main_list.remove(rest)
                    await interaction.message.edit(content=f'**__{msg.content} has been removed.__**', view=self)
                    return
            await interaction.message.edit(content=f'**__Error: {msg.content} is not in the list.__**', view=self)

            self.normal_restaurant = self.main_list

    @app_commands.command(description="Sends a message with buttons to give you options on possible food choices")
    async def feedme(self, interaction:discord.Interaction):
        """Sends a menu with options regarding restaurants
        Sends a view that ontains buttons with options to add or remove a restaurant
        or randomly select a vegan or non-vegan restaurant
        """

        await interaction.response.send_message(view=self.GourmetMenu(cog=self))
        await log(self.bot, f'{interaction.user} ran /feedMe in `#{interaction.channel}`')

    async def write_restaurants(self):
        self.restaurants.to_csv('assets/restaurants.csv', index=False)