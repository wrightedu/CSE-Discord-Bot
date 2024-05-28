import csv
import os
import pandas as pd

from discord.ui import View
from discord.ext import commands
from discord import app_commands

from utils.utils import *
from utils.db_utils import initialize_db, insert_user, create_connection, insert_timesheet, insert_pomodoro, get_timesheet_id

async def setup(bot):
    cwd = (os.path.dirname(os.path.abspath(__file__)))
    directory = os.path.dirname(cwd)
    db_path = os.path.join(directory, "cse_discord.db")
    if not os.path.exists(db_path):
        initialize_db(db_path)
    else:
        print("Database already exists")

    await bot.add_cog(Checkin(bot))

class Checkin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class CreatePomodoro(discord.ui.Modal, title='Pomodoro Creation'):
        name = discord.ui.TextInput(label='What issue are you working on?')

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """ An event listener to check for different checkin button presses.
            Verifies that the interaction includes a custom_id. Each individual statement
            checks to make sure that the interaction contains a specific custom_id.
        """
        if interaction.data is not None and 'custom_id' in interaction.data and interaction.data['custom_id'] is not None:
            if 'checkin_checkin_btn' in interaction.data['custom_id']:
                time = str(await get_time_epoch())
                conn = create_connection("cse_discord.db")

                timesheet = insert_timesheet(conn, interaction.user.id, time)

                await update_view(interaction, Checkin.checkedInView())
                await interaction.response.send_message("You have checked in!", ephemeral=True)
            elif 'checkedin_pomo_btn' in interaction.data['custom_id']:
                modal = discord.ui.Modal(title="Pomodoro Creation", custom_id=f"checkedin_pomo_create_{interaction.message.id}")
                modal.add_item(discord.ui.TextInput(label="What issue are you working on", required=True))

                await interaction.response.send_modal(modal)
            elif 'checkedin_pomo_create' in interaction.data['custom_id']:
                conn = create_connection("cse_discord.db")
                timesheet_id = get_timesheet_id(conn, interaction.user.id)
                time = str(await get_time_epoch())
                pomo_reason = interaction.data['components'][0]['components'][0]['value']
                pomo = insert_pomodoro(conn, timesheet_id, pomo_reason, time)

                channel = interaction.channel
                message_id = int(interaction.data['custom_id'].replace("checkedin_pomo_create_", ""))

                message = await channel.fetch_message(message_id)
                await message.edit(view=Checkin.pomoView())

                await interaction.response.send_message("You have started a pomodoro. I will check with you in 20 minutes", ephemeral=True)


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

        time = str(await get_time_epoch())

        conn = create_connection("cse_discord.db")
        status = insert_user(conn, discord_id, discord_user, time)
        conn.close()

        if status == "User already exists":
            await interaction.response.send_message("ERROR: You are already registered", ephemeral=True)
            return
        elif status == "Could not connect to database":
            await interaction.response.send_message("ERROR: Unable to connect to database", ephemeral=True)
            return
        elif status == "Error":
            await interaction.response.send_message("Error registering for checkin", ephemeral=True)
            return

        view = Checkin.checkInView()
        channel = await interaction.user.create_dm()

        await channel.send(view=view)
        await interaction.response.send_message("A DM has been sent to you", ephemeral=True)
