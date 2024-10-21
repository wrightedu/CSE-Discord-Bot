# imports Discord 
import asyncio
from discord import app_commands
from discord.ext import commands
from zipfile import ZipFile 
from utils.utils import *
import os
import subprocess
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


    def get_moss_id(discord_id):
        """Gets a user's MossID
        Uses a provided discord_id (from the calling command's interaction) to search the CSV for the associated MossID

        Args:
            discord_id (int): the discord id of the user

        Returns:
            string: the moss id associated with the user's discord id or none if the user is not in the CSV
        """

        # Assign the CSV to a variable and create a pandas dataframe
        csv_filepath = "assets/moss_ids.csv"
        moss_df = pd.read_csv(csv_filepath)

        if discord_id in moss_df["discord_id"].values:
            return moss_df.loc[moss_df["discord_id"] == discord_id]["moss_id"].values[0]
        else:
            # From /moss, we can check if 'none' was returned and send a message to the user
            return None


    async def delete_all(dir_path):
        """Delete all files and directories
        Delete's all files and directories below the directory specified by the path
        passed into the function.

        Args:
            dir_path (string): Directory to remove all contents from

        Outputs:
            An error if raised.
        """
        try:
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isdir(file_path):
                    try:
                        os.rmdir(file_path)
                    except Exception as e:
                        await MOSS.delete_all(file_path)
                        os.rmdir(file_path)
                elif os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Could not delete {file}. Error: {e}")


    async def check_moss_folder(dir_path):
        """If a folder for the moss user does not exist, creates one at the specified path. If one already exists but
        has contents, deletes all contents.

        Args:
            dir_path (string): Path to new or
        """
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        
        if len(os.listdir(dir_path)) > 0:
            await MOSS.delete_all(dir_path)


    @app_commands.command(description="This will check if students are cheaters") #they ALL are
    @app_commands.default_permissions(administrator=True)
    async def moss(self, interaction:discord.Interaction):
        """ Run MOSS command
        Will take in the .zip file from the user and run Ali Aljaffer's code on it, which will then run the perl script

        Args:
            upload_file (file): similar to course management upload file

        Outputs:
            MOSS URL
        """

        moss_id = MOSS.get_moss_id(interaction.user.id)
        if moss_id is None:
            await interaction.response.send_message("You do not have a MossID associated with your account. Please register your MossID with /moss_register first")
            return

        mosspath = f"/tmp/{moss_id}"
        await MOSS.check_moss_folder(mosspath)

        # copied and pasted - needs fixed
        await interaction.response.send_message("Please attach a .zip file of all student code!")

        try:
            # saves file to the name of the .ZIP file that is given by the user
            # waits for 1 minute for the file to be uploaded
            file = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user, timeout=60.0)
        except asyncio.TimeoutError:
            # if the user takes too long, the process will timeout and this message will be returned back
            await interaction.followup.send("Took too long to upload file. Please try again.")
            return
        
        # gives the user the ability to cancel the program if they want to
        if file.content.lower() in ["cancel", "exit", "stop"]:
            await interaction.followup.send("/moss cancelled")
            return

        zip_filepath = f"{mosspath}/bob.zip"

        # if there are more than 0 attachments, the code will continue
        # if it's not, the bot will yell at the user
        if len(file.attachments) > 0:
            if not file.attachments[0].filename.endswith(".zip"):
                await interaction.followup.send("Please attach a .zip file. Please rerun.")
                return
        else:
            await interaction.followup.send("Please attach a populated .zip file. Please rerun.")
            return

        # saves .zip file
        await file.attachments[0].save(zip_filepath)

        moss_command = f"python3 ./utils/WSU_mossScript.py --id {moss_id}"

        process = subprocess.Popen(
            moss_command, stdout = subprocess.PIPE, shell=True)

        await interaction.channel.send("Running MOSS (This can sometimes take 30+ seconds)...")

        output = process.communicate()[0]

        # Splits the output by newline and gets the last line, which is the moss link
        link = output.decode().split("\n")[-2]

        await interaction.followup.send(link)


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
            await interaction.response.send_message("Invalid MossID. Please try again.",ephemeral=True)
            return

        # Checks if the discord_id is already int the CSV, and if it is, it will return the moss_id. If not, 
        # it will add the given moss_id to the CSV
        if discord_id in moss_df["discord_id"].values:
            found_moss_id = moss_df.loc[moss_df["discord_id"] == discord_id]["moss_id"].values[0]
            await interaction.response.send_message(f"Your account is already registered with the associated MossID: `{found_moss_id}`\nWould you like to update your MossID? (y/n)", ephemeral=True)

            update = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)

            # If they wish to update their MossID, update it in the CSV
            if update.content.lower() == "y":
                moss_df.loc[moss_df["discord_id"] == discord_id, "moss_id"] = moss_id
                moss_df.to_csv(csv_filepath, index=False)
                await log(self.bot, f"{interaction.user} ran /moss_register in #{interaction.channel} and updated their MossID in the CSV")
                await interaction.followup.send(f"The new MossID: `{moss_id}`, is now associated with your account in the CSV", ephemeral=True)
            else:
                await interaction.followup.send("Your MossID has not been updated.", ephemeral=True)

            return
        else:
            new_row_df = pd.DataFrame([{"discord_id": discord_id, "moss_id": moss_id}])
            moss_df = pd.concat([moss_df, new_row_df], ignore_index=True)
            moss_df.to_csv(csv_filepath, index=False)
            await log(self.bot, f"{interaction.user} ran /moss_register in #{interaction.channel} and added their MossID to the CSV")
            await interaction.response.send_message(f"The MossID: `{moss_id}`, has been added to the CSV and is associated with your account",ephemeral=True)
