import csv
import os
import pandas as pd

from discord.ui import View
from discord.ext import commands
from discord import app_commands

from utils.utils import *
from utils.db_utils import initialize_db, insert_user, create_connection

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

    def checkInView():
        """Function that returns the check in view upon registration
        The Check-in View will contain a button to allow a user to check-in

        Outputs:
            view (discord.ui.View) - The view containing the checkin
        """


        view = View()
        checkin_button = discord.ui.Button(label="Check-in", style=discord.ButtonStyle.green, custom_id="checkin_checkin_btn")
        view.add_item(checkin_button)

        return view

    def checkedInView():
        """Function that returns the checked-in view
        The Checked-in View will contain a button to allow a user to check-out, as well as a button
        for a user to start a pomodoro

        Outputs:
            view (discord.ui.View) - The view containing the checkout and pomo buttons
        """

        view = View()

        checkout_button = discord.ui.Button(label="Check-out", style=discord.ButtonStyle.red, custom_id="checkedin_checkout_btn")
        pomo_button = discord.ui.Button(label="Pomodoro", style=discord.ButtonStyle.blurple, custom_id="checkedin_pomo_btn")

        view.add_item(checkout_button)
        view.add_item(pomo_button)

        return view
    
    def pomoView():
        """ Function that returns the pomo view
        The pomo View will contain buttons to finish your pomodoro, report that you are blocked, and not done.

        Outputs:
            view(discord.ui.View) - The view containing the pomodoro view buttons
        """
        
        view = View()

        done_button = discord.ui.Button(label="Done", style=discord.ButtonStyle.green, custom_id="pomo_done_btn")
        blocked_button = discord.ui.Button(label="Help/Blocked", style=discord.ButtonStyle.red, custom_id="pomo_blocked_btn")
        not_done_button = discord.ui.Button(label="Not Done", style=discord.ButtonStyle.secondary, custom_id="pomo_not_done_btn")

        view.add_item(done_button)
        view.add_item(blocked_button)
        view.add_item(not_done_button)

        return view

    @app_commands.command(name="checkin-register", description="Register for checkin/timesheets!")
    async def checkin_register(self, interaction:discord.Interaction):
        """Allows a user to register for a check-in
        This function will insert the user into the database and send a DM to the user

        Outputs:
            A placeholder message to confirm a DM was sent to the user
        """

        discord_id = interaction.user.id
        discord_user = interaction.user.name

        time = str(get_time_epoch())

        conn = create_connection("cse_discord.db")
        insert_user(conn, discord_id, discord_user, time)
        conn.close()

        view = Checkin.checkInView()
        channel = await interaction.user.create_dm()

        await channel.send(view=view)
        await interaction.response.send_message("A DM has been sent to you", ephemeral=True)
