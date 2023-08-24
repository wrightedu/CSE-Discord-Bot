import csv
import os
import pandas as pd
from typing import List
from validators import url

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
        
        if (issue_link.content.casefold() == "none" or not url(issue_link.content)):
            task_as_list = [interaction.user.id, task_name.content, task_num, '', "Incomplete", 0]
            await channel.send("No valid link was entered, task is still being created...")
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
            An embedded discord message that displays the user's tasks in column format
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
            link = tasks_df.loc[index, 'link']
            if (row['userid'] == interaction.user.id and row['status'] == "Incomplete"):
                if url(str(link)):
                    names += f"[{row['name']}]({link})\n"
                else:
                    names += f"{row['name']}\n"
                task_ids += f"{row['number']}\n"
                time_spent += f"{row['time spent']}\n"

        embed.add_field(name="**Tasks**", value=names)
        embed.add_field(name="**ID's**", value=task_ids)
        embed.add_field(name="**Time Spent**", value=time_spent)

        await channel.send(embed=embed)

    async def complete(self, interaction:discord.Interaction, filepath:str, channel:discord.DMChannel):
        """A function that marks a task as completed
        Marks a specified task as completed in the status column of the csv

        Args:
            filepath (str): String representation of the path to the csv file
            channel (discord.Channel): Channel to send the discord messages to

        Outputs:
            Sends a followup message either confirming the task was completed, or a message saying it could not be completed
        """
        
        tasks_df = pd.read_csv(filepath)

        await channel.send("Enter the ID of the task you wish to mark as complete")
        task_id = await self.bot.wait_for('message', check=lambda message: message.author == interaction.user)
        try:
            int(task_id.content)
        except:
            await channel.send("Not a valid ID")
            return

        for index, row in tasks_df.iterrows():
            if (row['userid'] == interaction.user.id and row['number'] == int(task_id.content) and row['status'] == "Incomplete"):
                tasks_df.loc[index, 'status'] = 'Complete'
                tasks_df.to_csv(filepath, index=False)

                await channel.send(f'Task "{row["name"]}" with ID "{task_id.content}" has been completed.')
                return

        await channel.send("Nothing has been marked as complete as either the ID was not found, wasn't your task, or was already completed")

    @app_commands.command(description="Add, list, or mark your tasks as complete")
    async def task(self, interaction:discord.Interaction, option:str):
        """Create and manage tasks
        A function designed to allow the user to track small tasks
        to increase productivity. Gives the user the option to create a new task,
        list all incomplete tasks, or mark a specific task as complete.

        Args:
            option (str): Autocomplete parameter to allow the user to choose between creating, listing, or completing a task
        
        """
        await interaction.response.send_message("Check your DM's", ephemeral=True)

        csv_filepath = f'assets/tasks.csv'
        if not (os.path.exists(csv_filepath)):
            file = open(csv_filepath, "w")
            file.write("userid,name,number,link,status,time spent\n")
            file.close()

        channel = await interaction.user.create_dm()

        if (option == "Add"):
            await self.add_task(interaction, csv_filepath, channel)
        elif (option == "List"):
            await self.list_tasks(interaction, csv_filepath, channel)
        elif (option == "Mark Completed"):
            await self.complete(interaction, csv_filepath, channel)

    # Autocomplete functionality for the parameter "cog_name" in the load, reload, and unload commands
    @task.autocomplete("option")
    async def task_auto(self, interaction:discord.Interaction, current:str) -> List[app_commands.Choice[str]]:
        data = []
        choices = ["Add", "List", "Mark Completed"] 
        # For every choice if the typed in value is in the choice add it to the possible options
        for choice in choices:
            if current.lower() in choice.lower():
                data.append(app_commands.Choice(name=choice, value=choice))
        return data
