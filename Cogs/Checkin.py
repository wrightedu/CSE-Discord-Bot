import csv
import os
import pandas as pd

from discord.ui import View
from discord.ext import commands
from discord import app_commands

from utils.utils import *

async def setup(bot):
    await bot.add_cog(Checkin(bot))

class Checkin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class CheckinView(View):
        @discord.ui.button(label="Check-in", style=discord.ButtonStyle.green)
        async def checkin(self, interaction:discord.Interaction, button:discord.ui.Button):
            """A button that will create a timesheet for the user in the SQLite database"""

            # This will eventually have some database interaction
            await interaction.response.send_message("You have checked in! (not really)")
