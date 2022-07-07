import discord
from discord.ext import commands
from discord.ui import view

class Button(discord.ui.View):

    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="Blurple Button",style=discord.ButtonStyle.blurple) # or .primary
    async def blurple_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        button.style=discord.ButtonStyle.green
        await interaction.response.edit_message(view=self)
        print("hello")