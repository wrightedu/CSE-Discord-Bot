# imports Discord 
from discord import app_commands
from discord.ext import commands
from zipfile import ZipFile 
from utils.utils import *
import os
import pandas as pd

# adds my cog to the bot
async def setup(bot:commands.Bot):
    # Might want to make this a global class variable at some point(?)
    csv_filepath = "assets/moss_ids.csv"

    # If the moss_ids.csv does not exist on startup, create it
    if not os.path.exists(csv_filepath):
        with open(csv_filepath, 'w') as file:
            # Add the header for the df
            file.write("discord_id,moss_id\n")
    await bot.add_cog(MOSS(bot))

# constructor method that passes in Cog commands
class MOSS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    
    @app_commands.command(description="This will check if students are cheaters") # they ALL are
    @app_commands.default_permissions(administrator=True)
    async def test(self, interaction:discord.Interaction):
        """ Run MOSS command
        Idk

        Args:
            upload_file (file): similar to course management upload file

        Outputs:
            MOSS URL
        """

        # TODO change mosspath to /tmp/<mossuser>
        mosspath = "/tmp/moss"
        if not os.path.exists(mosspath):
            os.mkdir(mosspath)

        # copied and pasted - needs fixed
        await interaction.response.send_message("Please attach a .zip file of all student code!")

        # saves file to the name of the .ZIP file that is given by the user
        file = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

        # TODO change bob.zip to <datestamp>.zip
        zip_filepath = f"{mosspath}/bob.zip"
        # if there are more than 0 attachments, the code will continue
        # if it's not, the bot will yell at the user
        while not len(file.attachments) > 0:
            await interaction.followup.send("I need a populated .zip file.")
            file = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

        await file.attachments[0].save(zip_filepath)

        # here I need to unzip the file in zip_filepath
        with ZipFile(zip_filepath, 'r') as code_zip:
            code_zip.extractall(path=mosspath)


    @app_commands.command(description="Register a new MossID")
    @app_commands.checks.has_any_role("Teaching Assistant", "Faculty", "cse-devteam", "cse-support")
    async def moss_register(self, interaction:discord.Interaction, moss_id:str):
        """Adds new user's DiscordID and MossID to the CSV
        Allows a user to register their MossID and associate it to their DiscordID in the CSV. If the user already has a MossID
        associated with their DiscordID, they will be given the option to update their MossID. If they do not wish to update
        their MossID, command execution will terminate.

        Args:
            moss_id (string): the moss id to be added to the csv

        Outputs:
            Adds a connected DiscordID and MossID to the CSV
        """
        # Assign the CSV to a variable and create a pandas dataframe
        csv_filepath = "assets/moss_ids.csv"
        moss_df = pd.read_csv(csv_filepath)

        # Assign the user's discord id to a variable
        discord_id = interaction.user.id

        # Verify that the given moss_id is valid 
        # From what I have seen, moss_id's are 8 or 9 digits long. This check can be removed if we find out otherwise
        if not moss_id.isdigit() or not (len(moss_id) == 8 or len(moss_id) == 9):
            await interaction.response.send_message("Invalid MossID. Please try again.")
            return

        # Checks if the discord_id is already int the CSV, and if it is, it will return the moss_id. If not, 
        # it will add the given moss_id to the CSV
        if discord_id in moss_df["discord_id"].values:
            found_moss_id = moss_df.loc[moss_df["discord_id"] == discord_id]["moss_id"].values[0]
            await interaction.response.send_message(f"Your account is already registered with the associated MossID: `{found_moss_id}`\nWould you like to update your MossID? (y/n)")

            update = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # If they wish to update their MossID, update it in the CSV
            if update.content.lower() == "y":
                moss_df.loc[moss_df["discord_id"] == discord_id, "moss_id"] = moss_id
                moss_df.to_csv(csv_filepath, index=False)
                await log(self.bot, f"{interaction.user} ran /moss_register in #{interaction.channel} and updated their MossID in the CSV")
                await interaction.followup.send(f"The new MossID: `{moss_id}`, is now associated with your account in the CSV")
            else:
                await interaction.followup.send("Your MossID has not been updated.")

            return
        else:
            new_row_df = pd.DataFrame([{"discord_id": discord_id, "moss_id": moss_id}])
            moss_df = pd.concat([moss_df, new_row_df], ignore_index=True)
            moss_df.to_csv(csv_filepath, index=False)
            await log(self.bot, f"{interaction.user} ran /moss_register in #{interaction.channel} and added their MossID to the CSV")
            await interaction.response.send_message(f"The MossID: `{moss_id}`, has been added to the CSV and is associated with your account")
