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

    async def add_task(interaction:discord.Interaction, filepath:str):
        channel = await interaction.user.create_dm()
        await channel.send("Enter the name of the task!")
        msg = await interaction.bot.wait_for('message', check=lambda message: message.author == interaction.user)


    @app_commands.command(description="Add, list, or mark your tasks as complete")
    async def task(self, interaction:discord.Interaction, task:str,  option:str, issue: str = 'None'):
        """A function designed to allow the user to track small tasks
        to increase productivity. 
        
        Outputs: 
            DM task list to user.
        """
        await interaction.response.send_message("Check your DM's", ephemeral=True)

        # options = [task]
        # if (issue != 'None'):
        #     options.append(issue)

        channel = await interaction.user.create_dm()

        csv_filepath = f'assets/Tasklists/tasks.csv'
        if not (os.path.exists(csv_filepath)):
            file = open(csv_filepath, "w")
            file.write("name,number,link,status,#pomos")
            file.close()
            tasks_df = pd.read_csv(csv_filepath)

        if (option == "Add"):
            self.add_task(interaction, csv_filepath)

        task_numbers = tasks_df["number"].to_list()

        if (len(task_numbers) != 0):
            task_num = task_numbers[-1] + 1
        else:
            task_num = 1    

        await channel.send(f'Task: {task}; Num: {task_num}; URL: {issue}')

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

