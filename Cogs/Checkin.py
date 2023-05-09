from discord.ui import Button
from discord.ui import View
from discord.ext import commands
from discord import app_commands

from utils.utils import *

async def setup(bot):
    await bot.add_cog(Checkin(bot))

class Checkin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="")
    @app_commands.default_permissions(administrator=True)
    async def task(self, interaction:discord.Interaction, amount:str):

        #Checkout button that displays a message that the user has finished their tasks.
        task_view = View(timeout=None)
        


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
            await interact.channel.send(f'What are you working on?', ephemeral=True)
            msg = await self.bot.wait_for('message', check=lambda message: message.author == interact.user)
            print(msg.content)
            

            done.callback = self.done_on_click
            not_done.callback = self.not_done_on_click
            self.task = msg.content
        

        async def done_on_click(self, interaction:discord.Interaction):
            timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(content=f"{interaction.user.display_name} completed {self.task} @{timestamp}")


        async def not_done_on_click(self, interaction:discord.Interaction):
            timestamp = datetime.datetime.now().strftime(r"%I:%M %p")
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(content=f"{interaction.user.display_name} did not complete {self.task} @{timestamp}")
