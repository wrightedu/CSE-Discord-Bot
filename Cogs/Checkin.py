import csv
import os
from datetime import time
import pandas as pd
import time
import re

from discord.ui import View
from discord.ext import commands, tasks
from discord import app_commands

from utils.utils import *
from utils.db_utils import (
    initialize_db, 
    insert_user, 
    create_connection, 
    insert_timesheet, 
    insert_pomodoro, 
    update_timesheet, 
    get_timesheet_id, 
    get_timesheet, 
    get_pomodoro_id, 
    get_pomodoro, 
    update_pomodoro, 
    insert_user_help, 
    get_all_open_pomodoros, 
    get_all_open_timesheets, 
    close_all_pomodoros, 
    get_user_report, 
    update_pomo_rewards
)

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
        self.check_pomodoros.start()
        self.check_timesheets.start()

    def cog_unload(self):
        self.check_pomodoros.cancel()
        self.check_timesheets.cancel()

    check_in_group = app_commands.Group(name="checkin", description="...")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """ An event listener to check for different checkin button presses.
            Verifies that the interaction includes a custom_id. Each individual statement
            checks to make sure that the interaction contains a specific custom_id.
        """
        if interaction.data is not None and 'custom_id' in interaction.data and interaction.data['custom_id'] is not None and not interaction.response.is_done():
            if 'checkin_checkin_btn' in interaction.data['custom_id']:
                time = str(await get_time_epoch())
                conn = create_connection("cse_discord.db")

                timesheet = insert_timesheet(conn, interaction.user.id, time)

                await update_view(interaction, Checkin.checked_in_view())
                await change_checkin_status(self.bot, interaction.user.id, interaction.user.display_name, 'checkin')
                await interaction.response.send_message("You have checked in!", ephemeral=True)
            elif 'checkedin_pomo_btn' in interaction.data['custom_id']:
                modal = discord.ui.Modal(title="Pomodoro Creation", custom_id=f"checkedin_pomo_create_{interaction.message.id}")
                modal.add_item(discord.ui.TextInput(label="What issue are you working on?", required=True))

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
                await message.edit(view=Checkin.pomo_view())

                await change_checkin_status(self.bot, interaction.user.id, interaction.user.display_name, 'pomodoro')
                await interaction.response.send_message("You have started a pomodoro. I will check with you in 20 minutes", ephemeral=True)
            elif 'checkedin_checkout_btn' in interaction.data['custom_id']:
                conn = create_connection("cse_discord.db")
                time_id = get_timesheet_id(conn, interaction.user.id)
                timesheet = get_timesheet(conn, time_id, interaction.user.id)

                time_in = float(timesheet[2])
                time_out = await get_time_epoch()
                total_time = time_out - time_in

                timesheet = update_timesheet(conn, time_id, interaction.user.id, time_in, time_out, total_time)
                
                if timesheet is True:
                    await update_view(interaction, Checkin.checkin_view())
                    await change_checkin_status(self.bot, interaction.user.id, interaction.user.display_name, 'checkout')
                    await interaction.response.send_message(f"You have now been clocked out. Total time: **{await get_string_from_epoch(total_time)}**", ephemeral=True)
                else:
                    await interaction.response.send_message("Error while checking out", ephemeral=True)
            elif 'pomo_done_btn' in interaction.data['custom_id'] or 'pomo_not_done_btn' in interaction.data['custom_id']:
                conn = create_connection("cse_discord.db")
                pomo_id = get_pomodoro_id(conn, interaction.user.id)
                time_id = get_timesheet_id(conn, interaction.user.id)
                pomo = get_pomodoro(conn, pomo_id, time_id)

                if pomo is not None:
                    time_start = float(pomo[3])
                    time_end = await get_time_epoch()
                    total_time = time_end - time_start

                    pomodoro = update_pomodoro(conn, pomo_id, time_id, pomo[2], time_start, time_end, total_time,
                                                str(3 if 'pomo_done_btn' in interaction.data['custom_id'] else 2), pomo[7])

                    if True is not None:
                        if pomo[6] == 1:
                            async for message in interaction.channel.history(limit=10):
                                if message.author.id == self.bot.user.id:
                                    await message.delete()
                                    break
                        
                        await change_checkin_status(self.bot, interaction.user.id, interaction.user.display_name, 'checkin')
                        await update_view(interaction, Checkin.checked_in_view())
                        if "pomo_done_btn" in interaction.data['custom_id']:
                            message = await update_pomo_rewards(conn, interaction.user.id)

                            if message is not None:
                                guild = None
                                for temp_guild in self.bot.guilds:
                                    if any(name in temp_guild.name for name in ['WSU CSE-EE Department', 'CSE Testing Server']):
                                        guild = temp_guild

                                # If guild was found
                                if guild is not None:
                                    role = discord.utils.get(guild.roles, name=message)
                                    
                                    member = await guild.fetch_member(interaction.user.id)

                                    await member.add_roles(role)
                                else:
                                    print("Guild none")

                        await interaction.response.send_message(f"You have now completed your pomodoro. Total time: **{await get_string_from_epoch(total_time)}**", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Error! Unable to close pomodoro", ephemeral=True)
            elif 'pomo_blocked_btn' in interaction.data['custom_id']:
                conn = create_connection("cse_discord.db")
                pomo_id = get_pomodoro_id(conn, interaction.user.id)
                time_id = get_timesheet_id(conn, interaction.user.id)
                pomo = get_pomodoro(conn, pomo_id, time_id)

                if pomo is not None:
                    modal = discord.ui.Modal(title="Pomodoro Blocked", custom_id="pomo_blocked_create")
                    modal.add_item(discord.ui.TextInput(label="What issue are you having?", required=True))

                    await interaction.response.send_modal(modal)
            elif 'pomo_blocked_create' in interaction.data['custom_id']:
                conn = create_connection("cse_discord.db")
                pomo_id = get_pomodoro_id(conn, interaction.user.id)
                time_id = get_timesheet_id(conn, interaction.user.id)
                pomo = get_pomodoro(conn, pomo_id, time_id)

                if pomo is not None:
                    pomodoro = update_pomodoro(conn, pomo_id, time_id, pomo[2], pomo[3], None, None, None, str(1 if pomo[7] is None else int(pomo[7]) + 1))
                    remark = interaction.data['components'][0]['components'][0]['value']
                    help = insert_user_help(conn, remark, pomo_id)

                    if help is not None:
                        await interaction.response.send_message(f"Your issue has been recorded", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Error!", ephemeral=True)

    def checkin_view():
        """Function that returns the check in view upon registration
        The Check-in View will contain a button to allow a user to check-in

        Outputs:
            view (discord.ui.View) - The view containing the checkin
        """


        view = View()
        checkin_button = discord.ui.Button(label="Check-in", style=discord.ButtonStyle.green, custom_id="checkin_checkin_btn")
        view.add_item(checkin_button)

        return view

    def checked_in_view():
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
    
    def pomo_view():
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

    @check_in_group.command(name="register", description="Register for checkin/timesheets!")
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

        view = Checkin.checkin_view()
        channel = await interaction.user.create_dm()

        await channel.send(view=view)
        await interaction.response.send_message("A DM has been sent to you", ephemeral=True)

    @check_in_group.command(name="clear", description="Clear your messages from the bot and reset timesheets")
    async def checkin_clear(self, interaction:discord.Interaction):
        """Allows a user to clear their DMs with the bot and reset their checkin states.
        This command will also send a new checkin embed
        
        Outputs:
            A new embed for timesheets
        """
        channel = await interaction.user.create_dm()
        if channel.id == interaction.channel_id:
            await interaction.response.defer(ephemeral=True)
            await Checkin.clemessage.followup.send("Up to 10 direct messages cleared. If you were clocked in, you've also been clocked out", ephemeral=True)
        else:
            await interaction.response.send_message("Cannot clear outside of your DMs", ephemeral=True)

    async def clear_checkin_messages(self, channel:  discord.TextChannel, user: discord.User):
        async for message in channel.history(limit=10):
            if message.author.id == self.bot.user.id:
                await message.delete()
        
        conn = create_connection("cse_discord.db")

        # Clear timesheet if open
        time_id = get_timesheet_id(conn, user.id)
        if time_id is not None:
            timesheet = get_timesheet(conn, time_id, user.id)

            time_in = float(timesheet[2])
            time_out = await get_time_epoch()
            total_time = time_out - time_in
 
            print(f"Conn: {conn}\nTime ID: {time_id}\nUser: {user.id}\nTime in: {time_in}\nTime out: {time_out}\nTotal time: {total_time}\n")
            update_timesheet(conn, time_id, user.id, time_in, time_out, total_time)

        # End pomodoro if open
        pomo_id = get_pomodoro_id(conn, user.id)
        if pomo_id is not None and time_id is not None:
            pomodoro = get_pomodoro(conn, pomo_id, time_id)

            time_start = float(pomodoro[3])
            time_end = await get_time_epoch()
            total_time = time_end - time_start

            update_pomodoro(conn, pomo_id, time_id, "", time_start, time_end, total_time, 2)

        conn.close()

        # Send new view
        await channel.send(view=Checkin.checkin_view())

    @tasks.loop(minutes=2.0)
    async def check_pomodoros(self):
        """ A task that checks open pomodoros every two minutes looking for pomodoros that need reminders
        """
        conn = create_connection("cse_discord.db")
        pomodoros = get_all_open_pomodoros(conn)

        if pomodoros is not None:
            for pomodoro in pomodoros:
                time = str(await get_time_epoch())
                if float(time) >= (float(pomodoro[3]) + (20*60)) and (pomodoro[6] == 0 or pomodoro[6] == None):
                    user = self.bot.get_user(int(pomodoro[8]))

                    if user is not None:
                        update_pomodoro(conn, pomodoro[0], pomodoro[1], pomodoro[2], pomodoro[3], pomodoro[4], pomodoro[5], 1, pomodoro[7])
                        channel = await user.create_dm()
                        await channel.send("According to my watch, 20 minutes has passed. How are things going?")
                elif float(time) >= (float(pomodoro[3]) + (8 * 60 * 60)) and pomodoro[6] == 1:
                    # Do things here if we ever want to change the automatic close time for pomodoros separately.
                    # Change the time delta above
                    while False:
                        user = self.bot.get_user(int(pomodoro[8]))

    @tasks.loop(minutes=5.0)
    async def check_timesheets(self):
        """ A task that checks open timesheets every five minutes looking for timesheets that need closed
        """
        conn = create_connection("cse_discord.db")
        timesheets = get_all_open_timesheets(conn)

        if timesheets is not None:
            for timesheet in timesheets:
                time = await get_time_epoch()
                
                if time >= (float(timesheet[2]) + (8 * 60 * 60)):
                    user = self.bot.get_user(int(timesheet[1]))

                    if user is not None:
                        total_time = time - float(timesheet[2])
                        update_timesheet(conn, timesheet[0], timesheet[1], timesheet[2], time, total_time)

                        close_all_pomodoros(conn, timesheet[0], time)

                        channel = await user.create_dm()
                        await change_checkin_status(self.bot, user.id, user.display_name, 'checkout')
                        await Checkin.clear_checkin_messages(self, channel, user)

    #TODO The get_report and get_montly_report function needs to be changed such that the output is presented to the user in a suitable and formatted fashion
    #Currently, it is set to output the SQL data to the terminal.

    # @check_in_group.command(name='report', description="Generate Report of the user's timesheet. Date Format should be in MM-DD-YYYY")
    # async def get_report(self, interaction: discord.Interaction, start_time:str = None, end_time:str = None):
    #     """
    #         Generates user report when requested by a USER
            
    #     """
    #     conn = create_connection("cse_discord.db")
    #     new_start_time = None if start_time is None else get_unix_time(start_time)
    #     new_end_time = None if end_time is None else get_unix_time(end_time)

    #     if start_time is None and end_time is None:
    #         #get the last pay period
    #         todays_date = time.time()
    #         monday = str(get_last_pay_period_monday(todays_date))
    #         datetime_obj = datetime.datetime.strptime(monday, '%Y-%m-%d')
    #         new_start_time = datetime_obj.timestamp()

    #         new_end_time = time.time()
    #         all_records, total_hours, complete_pomodoros = get_user_report(conn, interaction.user.id, new_start_time,new_end_time)
    #         print(all_records, total_hours, complete_pomodoros)
    #         await interaction.response.send_message("Look at the terminal log now, replace this later", ephemeral=True) #TODO replace this later

    #     elif start_time is not None and end_time is not None:
    #         all_records, total_hours, complete_pomodoros = get_user_report(conn, interaction.user.id, new_start_time,new_end_time)
    #         print("with data",all_records, total_hours, complete_pomodoros)
    #         await interaction.response.send_message("Look at the terminal log now, replace this later", ephemeral=True) #TODO replace this later
    #     else:
    #         await interaction.response.send_message("Please provide both dates for a given range or leave empty for your last pay period", ephemeral=True)


    # @check_in_group.command(name='report-monthly', description="Generate report of multiple user for the month. Date Format should be in MM-DD-YYYY")
    # # @app_commands.default_permissions(administrator=True)
    # async def get_montly_report(self, interaction: discord.Interaction, role:discord.Role, start_time:str, end_time:str):
    #     """
    #         Generates report for multiple user for admin level user

    #     """
    #     conn = create_connection("cse_discord.db")
    #     new_start_time = None if start_time is None else get_unix_time(start_time)
    #     new_end_time = None if end_time is None else get_unix_time(end_time)
    #     report = {}
    #     for member in role.members:
    #         if start_time is None and end_time is None:
    #             #get the last pay period
    #             todays_date = time.time()
    #             monday = str(get_last_pay_period_monday(todays_date))
    #             datetime_obj = datetime.datetime.strptime(monday, '%Y-%m-%d')
    #             new_start_time = datetime_obj.timestamp()

    #             new_end_time = time.time()
    #             all_records, total_hours, complete_pomodoros = get_user_report(conn, member.id, new_start_time,new_end_time)
    #             print(all_records, total_hours, complete_pomodoros)
    #             print("error when parsing date. Date Should NOT BE NONE and should be provided")

    #         elif start_time is not None and end_time is not None:
    #             all_records, total_hours, complete_pomodoros = get_user_report(conn, member.id, new_start_time,new_end_time)
    #             if not all_records and not complete_pomodoros:
    #                 print("No record found for ", member.id)
    #             else:
    #                 report[member.id] = [all_records, total_hours, complete_pomodoros]
                
    #         else:
    #             await interaction.response.send_message("Please provide both dates for a given range or leave empty for your last pay period", ephemeral=True)
        
    #     print("printing report for now \n", report)