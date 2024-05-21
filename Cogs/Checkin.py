import csv
import os
import pandas as pd

from discord.ui import View
from discord.ext import commands
from discord import app_commands

from utils.utils import *
from utils.db_utils import initialize_db


async def setup(bot):
    cwd = (os.path.dirname(os.path.abspath(__file__)))
    directory = os.path.dirname(cwd)
    db_path = os.path.join(directory, "cse_discord.db")
    if not os.path.exists(db_path):
        initialize_db(db_path)
    else:
        print("Database initialization failed")

    await bot.add_cog(Checkin(bot))

class Checkin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class CheckinView(View):
        @discord.ui.button(label="Check-in", style=discord.ButtonStyle.green)
        async def checkin(self, interaction:discord.Interaction, button:discord.ui.Button):
            """A button that will create a timesheet for the user in the SQLite database

            This will eventually have some database interaction

            Args:
                button (discord.ui.Button): the button that will be clicked to check in

            Outputs:
                A View with a button that will create a timesheet for the user in the SQLite database
            """

            # This will eventually have some database interaction
            await interaction.response.send_message("You have checked in! (not really)")

    async def checkedInView():
        view = View()

        check_out_button = discord.ui.Button(label="Check-out", style=discord.ButtonStyle.red, custom_id="checkoutbutton")
        pomo_button = discord.ui.Button(label="Pomodoro", style=discord.ButtonStyle.blurple, custom_id="pomobutton")

        view.add_item(check_out_button)
        view.add_item(pomo_button)

    @app_commands.command(name="checkin-register", description="Register for checkin/timesheets!")
    async def checkin_register(self, interaction:discord.Interaction):
        """Allows a user to register for a check-in

        This will eventually have some database interaction

        Outputs:
            A placeholder message to confirm a DM was sent to the user
        """

        discordID = interaction.user.id # for later use
        discordUser = interaction.user.name # for later use

        view = self.CheckinView()
        channel = await interaction.user.create_dm()

        await channel.send(view=view)
        await interaction.response.send_message("A DM has been sent to you", ephemeral=True)