import csv
import os
import pandas as pd
from typing import List
from validators import url

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

    async def add_task(self, interaction:discord.Interaction, filepath:str):
        channel = await interaction.user.create_dm()

        await channel.send("Enter the name of the task you wish to create")
        task_name = await self.bot.wait_for('message', check=lambda message: message.author == interaction.user)

        await channel.send("Enter the link to a Github issue if applicable.\nEnter `none` if there is no issue.")
        issue_link = await self.bot.wait_for('message', check=lambda message: message.author == interaction.user)

        tasks_df = pd.read_csv(filepath)
        task_numbers = tasks_df["number"].to_list()

        task_num = 1
        if (len(task_numbers) != 0):
            task_num = task_numbers[-1] + 1
        
        if (issue_link.content.casefold() == "none"):
            task_as_list = [task_name.content, task_num, '', "Incomplete", 0]
        else:
            task_as_list = [task_name.content, task_num, issue_link.content, "Incomplete", 0]

        csv_file = open(filepath, 'a')
        writer = csv.writer(csv_file)
        writer.writerow(task_as_list)
        csv_file.close()

        await channel.send(f'Task "{task_name.content}" with ID "{task_num}" has been created.')


    async def list_tasks(interaction:discord.Interaction, filepath:str):
        # do something here to list the tasks
        pass
    async def remove_tasks(interaction:discord.Interaction, filepath:str):
        # do something here to remove the tasks
        pass


    @app_commands.command(description="Add, list, or mark your tasks as complete")
    async def task(self, interaction:discord.Interaction, option:str):
        """A function designed to allow the user to track small tasks
        to increase productivity. 
        
        Outputs: 
            DM task list to user.
        """
        await interaction.response.send_message("Check your DM's", ephemeral=True)

        # options = [task]
        # if (issue != 'None'):
        #     options.append(issue)

        csv_filepath = f'assets/tasks.csv'
        if not (os.path.exists(csv_filepath)):
            file = open(csv_filepath, "w")
            file.write("name,number,link,status,#pomos")
            file.close()
            tasks_df = pd.read_csv(csv_filepath)

        if (option == "Add"):
            await self.add_task(interaction, csv_filepath)
        elif (option == "List"):
            #stuff here
            pass
        elif (option == "Remove"):
            #stuff here
            pass

    # Autocomplete functionality for the parameter "cog_name" in the load, reload, and unload commands
    @task.autocomplete("option")
    async def task_auto(self, interaction:discord.Interaction, current:str) -> List[app_commands.Choice[str]]:
        data = []
        choices = ["Add", "List", "Remove"] 
        # For every choice if the typed in value is in the choice add it to the possible options
        for choice in choices:
            if current.lower() in choice.lower():
                data.append(app_commands.Choice(name=choice, value=choice))
        return data

