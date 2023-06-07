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

    async def add_task(self, interaction:discord.Interaction, filepath:str, channel:discord.DMChannel):
        """A function that creates a task
        Creates and adds a task based on user input to the tasks.csv file

        Args:
            filepath (str): String representation of the path to the csv file
            channel (discord.Channel): Channel to send the discord messages to

        Outputs:
            Message to chat displaying the task name and number of the new task that was created
        """

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
            task_as_list = [interaction.user.id, task_name.content, task_num, '', "Incomplete", 0]
        else:
            task_as_list = [interaction.user.id, task_name.content, task_num, issue_link.content, "Incomplete", 0]

        csv_file = open(filepath, 'a')
        writer = csv.writer(csv_file)
        writer.writerow(task_as_list)
        csv_file.close()

        await channel.send(f'Task "{task_name.content}" with ID "{task_num}" has been created.')


    async def list_tasks(self, interaction:discord.Interaction, filepath:str, channel:discord.DMChannel):
        """A function that lists all tasks
        Lists the tasks that are currently in the tasks.csv

        Args:
            filepath (str): String representation of the path to the csv file
            channel (discord.Channel): Channel to send the discord messages to

        Outputs:
            
        """

        tasks_df = pd.read_csv(filepath)

        embed = discord.Embed(
            title = "Task List",
            description = "List of your incomplete tasks",
            colour = discord.Colour.from_rgb(3,105,55)
        )

        names = ""
        task_ids = ""
        time_spent = ""

        for index, row in tasks_df.iterrows():
            if (row['userid'] == interaction.user.id and row['status'] == "Incomplete"):
                names += f"{row['name']}\n"
                task_ids += f"{row['number']}\n"
                time_spent += f"{row['time spent']}\n"

        embed.add_field(name="**Tasks**", value=names)
        embed.add_field(name="**ID's**", value=task_ids)
        embed.add_field(name="**Time Spent**", value=time_spent)

        await channel.send(embed=embed)


    async def remove_tasks(self, interaction:discord.Interaction, filepath:str, channel:discord.DMChannel):
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

        csv_filepath = f'assets/tasks.csv'
        if not (os.path.exists(csv_filepath)):
            file = open(csv_filepath, "w")
            file.write("userid,name,number,link,status,time spent")
            file.close()

        channel = await interaction.user.create_dm()

        if (option == "Add"):
            await self.add_task(interaction, csv_filepath, channel)
        elif (option == "List"):
            await self.list_tasks(interaction, csv_filepath, channel)
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

