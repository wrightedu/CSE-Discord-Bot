import random
import copy

from discord.ui import View
from discord.ext import commands

from utils.utils import *


async def setup(bot):
    await bot.add_cog(Gourmet(bot))
    

class Gourmet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # count = 0
        self.normal_restaurant = []
        self.vegan_restaurant = []
        try:
            with open('assets/restaurants.txt') as f:
                for line in f:
                    line = line.strip()
                    if not self.normal_restaurant:
                        self.normal_restaurant = line.split(', ')
                    else:
                        self.vegan_restaurant = line.split(', ')
        except FileNotFoundError:
            print('Error: assets/restaurants.txt was not found on local machine.')


    # Menu that extends from a View
    class GourmetMenu(View):
        def __init__(self, *, cog, timeout=180):
            super().__init__(timeout=timeout)
            # self.cog = cog
            self.normal_restaurant = copy.deepcopy(cog.normal_restaurant)
            self.vegan_restaurant = copy.deepcopy(cog.vegan_restaurant)
            random.shuffle(self.normal_restaurant)
            random.shuffle(self.vegan_restaurant)


        # Returns a random restaurant
        @discord.ui.button(label="Random",style=discord.ButtonStyle.blurple,emoji='\U0001F3B1')
        async def random(self,interaction:discord.Interaction,button:discord.ui.Button):
            if not len(self.normal_restaurant) == 0:
                await interaction.response.edit_message(content='**' + self.normal_restaurant.pop() + '**', view=self)
            else:
                await interaction.response.edit_message(content='**__You have run out of restaurants. You are going to arbys.__**', view=self)
        
        # Adds a restaurant to a list
        @discord.ui.button(label="Add Restaurant",style=discord.ButtonStyle.green)
        async def add(self,interaction:discord.Interaction,button:discord.ui.Button):

            # This must be here because of the user response
            # If the user response is before this it would show "interaction failed"
            # The interaction has not really failed however it hasnt happened quick enough.
            await interaction.response.edit_message(content='**__Enter a restaurant to add to the list.__**', view=self)

            # Waiting for the user's response (with interactions!)
            msg = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # Turning the message to lowercase and appending it
            msg.content = msg.content.casefold()
            for rest in self.normal_restaurant:
                if msg.content == rest.casefold():
                    await interaction.message.edit(content=f'**__Error: {msg.content} already is in the restaurant list.__**', view=self)
                    return
            self.normal_restaurant.append(msg.content)

        # Removes a restaurant from a list
        @discord.ui.button(label="Remove Restaurant",style=discord.ButtonStyle.red)
        async def remove(self,interaction:discord.Interaction,button:discord.ui.Button):

            # This must be here because of the user response
            # If the user response is before this it would show "interaction failed"
            # The interaction has not really failed however it hasnt happened quick enough.
            await interaction.response.edit_message(content=f'**__Enter a restaurant to remove from the list.__**', view=self)

            # Waiting for the user's response (with interactons!)
            msg = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # Turning msg to lowercase
            msg.content = msg.content.casefold()

            # If the restaurant is not in the list it responds with an error
            for rest in self.normal_restaurant:
                if msg.content == rest.casefold():
                    self.normal_restaurant.remove(rest)
                    return
            await interaction.message.edit(content=f'**__Error: {msg.content} is not in the list.__**', view=self)
        
        # Returns a random vegan restaurant
        @discord.ui.button(label="Vegan",style=discord.ButtonStyle.blurple,emoji='\U0001F96C')
        async def vegan(self,interaction:discord.Interaction,button:discord.ui.Button):
            if not len(self.vegan_restaurant) == 0:
                await interaction.response.edit_message(content='**' + self.vegan_restaurant.pop() + '**', view=self)
            else:
                await interaction.response.edit_message(content='**__You have run out of restaurants. You are going to arbys.__**', view=self)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def feedme(self, ctx):
        await ctx.send(view=self.GourmetMenu(cog=self))
        await log(self.bot, f'{ctx.author} ran /feedMe in `#{ctx.channel}`')
