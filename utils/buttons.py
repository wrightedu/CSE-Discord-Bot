import discord
from discord.ext import commands
from discord.ui import view

class Button(discord.ui.View):

    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        
    def get_label():
        print("anything")
        return "self.label"

    def list_test(self, list_name):
        for x in self.children: # view elements, x is a button
            button = x
            button.label = "Label bro"
    #     for element in list_name:
    #         print(element)

    @discord.ui.button(label=get_label(),style=discord.ButtonStyle.blurple) # or .primary
    async def blurple_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        button.style=discord.ButtonStyle.green
        await interaction.response.edit_message(view=self)
        print("hello")
        print(self.label)


# create button and add to view (build button method/command)
#do that a bunch of times and don't care bout label (can leave blank)
#nother method to call after that sets all the labels in the view to their correct names
# maybe use custom id?