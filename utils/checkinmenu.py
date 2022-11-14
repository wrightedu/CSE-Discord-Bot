from discord.ui import Button
from discord.ui import View

from utils.utils import *

"""Button menu for the checkin command. Checkout, Help, and Pomodoro."""
class checkinmenu(View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.pomodoro = None
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
    async def Pomodoro(self, interact:discord.Interaction, button:discord.ui.Button):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        pomodoro = View(timeout=None)
        done = Button(label="Done", style=discord.ButtonStyle.green)
        not_done = Button(label="Not Done", style=discord.ButtonStyle.red)
        pomodoro.add_item(done)
        pomodoro.add_item(not_done)
        await interact.response.edit_message(view=pomodoro)
        self.pomodoro = pomodoro
        done.callback = self.done_on_click
        not_done.callback = self.not_done_on_click
    async def done_on_click(self, interaction:discord.Interaction):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        for child in self.pomodoro.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(content=f"{interaction.user.display_name} finished task @{timestamp}")
    async def not_done_on_click(self, interaction:discord.Interaction):
        timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
        for child in self.pomodoro.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(content=f"{interaction.user.display_name} did not finish task @{timestamp}")
