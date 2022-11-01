from discord.ui import View

from utils.utils import *

"""Button menu for the checkin command. Checkout, Help, and Pomodoro."""
class checkinmenu(View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    #Checkout button that displays a message that the user has finished their tasks.
    @discord.ui.button(label="Checkout", style=discord.ButtonStyle.green)
    async def checkout(self, interaction:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(content=f"{interaction.user.display_name} checked out @{timestamp}")
        
    #Help button that displays a message that the user needs help with a task.
    @discord.ui.button(label="HELP!", style=discord.ButtonStyle.red)
    async def HELP(self, interaction:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        await interaction.response.send_message(content=f"{interaction.user.display_name} sent out an SOS @{timestamp}")
    #Pomodoro button (IN PROGRESS).
    @discord.ui.button(label="Pomodoro", style=discord.ButtonStyle.blurple)
    async def Pomodoro(self, interaction:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        await interaction.response.send_message(content=f"I'm too lazy to figure out how to do this yet")
    