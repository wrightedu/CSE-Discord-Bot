from discord.ui import View

from utils.utils import *


class checkinmenu(View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Checkout", style=discord.ButtonStyle.green, emoji='\U0001F6D2')
    async def checkout(self, interaction:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        await interaction.response.send_message(content=f"{interaction.user.display_name} checked out @{timestamp}")
    
    @discord.ui.button(label="HELP!", style=discord.ButtonStyle.red,  emoji='\U0001F6D2')
    async def HELP(self, interaction:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        await interaction.response.send_message(content=f"{interaction.user.display_name} sent out an SOS @{timestamp}")
    
    @discord.ui.button(label="Pomodoro", style=discord.ButtonStyle.blurple, emoji='\U0001F6D2')
    async def Pomodoro(self, interaction:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        await interaction.response.send_message(content=f"I'm too lazy to figure out how to do this yet")
    