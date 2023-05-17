from discord.ui import Button
from discord.ui import View
from discord.ext import commands
from discord import app_commands
from validators import url
import pandas as pd
from utils.utils import *

async def setup(bot):
    await bot.add_cog(Checkin(bot))

class Checkin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Add, list, or mark your tasks as complete")
    async def task(self, interaction:discord.Interaction, task:str, issue: str = 'None'):
        """A function designed to allow the user to track small tasks
        to increase productivity. 
        
        Outputs: 
            DM task list to user.
        """
        await interaction.response.send_message("Check your DM's", ephemeral=True)
        options = [task]
        if (issue != 'None'):
            options.append(issue)
        channel = await interaction.user.create_dm()
        csv_filepath = f'assets/Tasklists/tasks.csv'
        if(does_file_exist(csv_filepath)):
            tasks_df = pd.read_csv(csv_filepath)
        else:
            header = "name,number,link,status,#pomos"
            create_csv(tasks.csv)
        task_numbers = tasks_df["number"].to_list()
        if (len(task_numbers) != 0):
            task_num = task_numbers[-1] + 1
        else:
            task_num = 1    
        await channel.send(f'Task: {task}; Num: {task_num}; URL: {issue}')



