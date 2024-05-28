import os
import re
import pandas as pd

from discord.ext import commands
from discord.utils import get
from discord.ui import View
from discord import app_commands

from utils.rolebutton import RoleButton
from utils.utils import *


async def setup(bot:commands.Bot):
    await bot.add_cog(CourseManagement(bot))


class CourseManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_category(self, interaction, category_names):
        """Verifies categories to be destroyed
        Looks through all categories and verifies if the list of category names is on the server

        Args:
            category_names (List[str]): a list of strings of the category names to delete

        Outputs:
            categories (List[categories]): a list of the verified categories.
        """

        # Get list of all categories (category objects) to be destroyed and print
        categories = []
        missing_categories = '__**MISSING FOLLOWING CATEGORIES**__\n'

        for category_name in category_names:
            category = get(interaction.guild.categories, name=category_name)

            # If the category was not found it adds it to the missing_categories message
            if category is None:
                missing_categories += f'{category_name}\n'
            else:
                categories.append(category)

        # only send if there are missing categories
        if not len(categories) == len(category_names):
            await interaction.channel.send(missing_categories)

        return categories

    async def get_roles(self, interaction, role_names):
        """Verifies roles to be destroyed
        Looks through all roles and verifies if the list of role names is on the server

        Args:
            role_names (List[str]): a list of strings of the role names to delete

        Outputs:
            roles (List[roles]): a list of the verified roles.
        """

        # Get list of all categories (category objects) to be destroyed and print
        roles = []
        missing_roles = '__**MISSING FOLLOWING ROLES**__\n'

        for role_name in role_names:
            role = get(interaction.guild.roles, name=role_name)

            # If the role was not found it adds it to the missing_roles message
            if role is None:
                missing_roles += f'{role_name}\n'
            else:
                roles.append(role)
        
        # only send if there are missing roles
        if not len(roles) == len(role_names):
            await interaction.channel.send(missing_roles)

        return roles

    @app_commands.command(description="Create course channels")
    @app_commands.default_permissions(administrator=True)
    async def build_courses(self, interaction:discord.Interaction):
        """Create course channels
        Try to destroy old course channels (calls on destroycourses)
        Read in role csv from cached file or from attachment on discord message
        Extract columns needed through a panda dataframe
        Get confirmation from author
        Create all categories, channels, and roles
        """

        await interaction.response.send_message("Please send CSV if you intend to use one. If you do not intend to use one, the cached CSV will be used.")
        csv_filepath = f'role_lists/roles_{interaction.guild.id}.csv'

        csv = await interaction.client.wait_for('message', check=lambda message: message.author == interaction.user)
        # If csv file attached, overwrite existing csv
        if len(csv.attachments) > 0:
            try:
                os.remove(csv_filepath)
            except FileNotFoundError:
                pass
            await csv.attachments[0].save(csv_filepath)
        
        courses_df = pd.read_csv(csv_filepath)

        # iterates through dataframe checking if a category exists
        # if it does, drop the row from the dataframe
        for i in range(len(courses_df)):
            if get(interaction.guild.categories, name=courses_df.loc[i, "text"]):
                courses_df.drop(index=i, axis=0, inplace=True)
        
        courses_df = courses_df.dropna(subset=['create_channels'])

        # extracts appropriate columns using a dataframe
        role_names = courses_df["role/link"].to_list()
        course_channels = courses_df["create_channels"].to_list()
        category_names = courses_df["text"].to_list()
        long_names = courses_df["long_name"].to_list()

        # Print to user list of channels to build
        message = '__**CREATE FOLLOWING CATEGORIES**__\n'
        for category_name in category_names:
            message += f'{category_name}\n'
        await interaction.channel.send(message)

        if not category_names:
            await interaction.channel.send("NO CATEGORIES TO BUILD")

        # Get confirmation before building channels
        if not await confirmation(self.bot, interaction, 'build'):
            return
        
        permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, 
                attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, 
                stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
        
        for i, role_name in enumerate(role_names):
            # Create roles
            role_name = role_names[i]
            role = await interaction.guild.create_role(name=role_name, permissions=permissions)
            role.mentionable = True
            
            # Create category
            category_name = category_names[i]
            category = await interaction.guild.create_category(category_name)
            await category.set_permissions(interaction.guild.default_role, read_messages=False)      # sets category to private
            await category.set_permissions(role, read_messages=True)        # allow role to see category
            
            # Create channels
            channels = course_channels[i].split(",")

            for channel in channels:
                # Create text channel
                if channel.startswith('#'):
                    await category.create_text_channel(channel, topic=long_names[i])
                # Create voice channel(s)
                else:
                    member_count, channel_name = channel.split('#')
                    if member_count == 0:
                        await category.create_voice_channel(channel_name)
                    else:
                        await category.create_voice_channel(channel_name, user_limit=int(member_count))
        await interaction.channel.send('***CATEGORIES AND ROLES HAVE BEEN BUILT***')

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def destroy_courses(self, interaction:discord.Interaction):
        """Destroy course channels
        Try loading in cached classlist csv
        Create list of all categories and roles to be deleted, send to author
        Get confirmation from author
        Delete all listed categories and roles
        """

        await interaction.response.defer(ephemeral=True)
        csv_filepath = f'role_lists/roles_{interaction.guild.id}.csv'
        try:
            courses_df = pd.read_csv(csv_filepath)
        except FileNotFoundError:
            await interaction.followup.send("File not found")

        # drop cross-listed courses (and other roles if on the file)
        courses_df = courses_df.dropna(subset=['create_channels'])
        
        # List of names of categories to be destroyed, as determined by saved csv
        category_names = courses_df['text'].tolist()
        categories = await self.get_category(interaction, category_names)

        # List of names of role to be destroyed, as determined by saved csv
        destroy_role_names = courses_df['role/link'].tolist()
        destroy_roles = await self.get_roles(interaction, destroy_role_names)
        
        message = '__**DESTROY FOLLOWING CATEGORIES**__\n'
        if len(categories):
            for category in categories:
                message += f'{category.name}\n'
        else:
            message += 'NO CATEGORIES FOUND\n'
        
        await interaction.channel.send(message)
        
        message = '__**DESTROY FOLLOWING ROLES**__\n'
        if len(destroy_roles):
            for role in destroy_roles:
                message += f'{role.name}\n'
        else:
            message += 'NO ROLES FOUND\n'

        await interaction.channel.send(message)

        if not await confirmation(self.bot, interaction, 'destroy'):
            await interaction.followup.send("Confirmation denied")
            return
        
        # Destroy categories and all subchannels
        for category in categories:
            for channel in category.channels:
                await channel.delete()
            await category.delete()
        
        for role in destroy_roles:
            await role.delete()

        await interaction.channel.send('***CATEGORIES AND ROLES HAVE BEEN DESTROYED***')
        await interaction.followup.send("Courses have been destroyed")

    async def rolemenu_callback(self, interaction:discord.Interaction, prefixes:list):
        """Callback function for buildrolemenu
        Creates role menus
        Find csv and extracts columns needed through a pandas dataframe
        Get confirmation from author when they wish to continue building the role menu despite missing roles in the server
        Create the buttons and put them in a view
        Send the role menu(s) consisting of the view(s) to the proper channel(s)

        Args:
            prefixes (list): used to access selected course-subject prefixes for role button creation

        Outputs:
            rolemenus that consist of rolebuttons
        """

        await interaction.response.defer()
        message = ""
        confirmation_message = ""

        csv_filepath = f'role_lists/roles_{interaction.guild.id}.csv'
        try:
            courses_df = pd.read_csv(csv_filepath)
        except FileNotFoundError:
            await interaction.channel.send("File not found")

        # iterates through dataframe checking if a role exists
        # if it doesn't, a confirmation message is created to display
        # roles that cannot be created 
        for i in range(len(courses_df)):
            if not get(interaction.guild.roles, name=courses_df.loc[i, "role/link"]):
                confirmation_message += f"{courses_df.loc[i, 'role/link']}\n"
                courses_df.drop(index=i, axis=0, inplace=True)

        # extracts appropriate columns using a dataframe
        category_names = courses_df["text"].to_list()
        long_names = courses_df["long_name"].to_list()
        role_names = courses_df["role/link"].to_list()

        if confirmation_message:
            confirmation_message = "**The following role(s) could not be found:**\n" + confirmation_message
            confirmation_message += "Would you like to continue building rolemenus?"
            await interaction.channel.send(confirmation_message)
            if not await confirmation(self.bot, interaction, 'confirm'):
                await interaction.channel.send("Confirmation denied")
                return

        for prefix in prefixes:
            # adds RoleButtons to a view with custom attributes and sends it to the appropriate channel
            channel_name = f'{prefix.lower()}-class-selection'
            channel = await get_channel_named(interaction.guild, channel_name)
            if channel is None:
                message += f"{channel_name} can't be found.\n"
                continue
            view = View(timeout=None)
            for i, role_name in enumerate(role_names):
                if re.match(prefix, category_names[i]):         # ensure prefix matches the course name (CEG, CS, EE)
                    if len(view.children) % 25 == 0 and len(view.children) != 0:          # limit of 25 components per view
                        await channel.send(view=view)
                        view = View(timeout=None)
                    this_button = RoleButton(button_name=f"{category_names[i]} - {long_names[i]}", role_name=role_names)
                    this_button.callback = this_button.on_click
                    view.add_item(this_button)
            if not view.children:
                message += f"No buttons were built for: {prefix}\n"
                continue
            await channel.send(view=view)
            message += f"Role buttons have been built for: {prefix}\n"
        await interaction.channel.send(message)

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def build_role_menu(self, interaction:discord.Interaction):
        """Creates rolemenu dropdown
        Creates options for class prefixes
        Creates a select menu (dropdown) using these options
        Calls rolemenu_callback when prefixes are selected
        Deletes the select menu after execution
        """

        options=[
            discord.SelectOption(label="CEG", description="Builds role menus for CEG"),
            discord.SelectOption(label="CS", description="Builds role menus for CS"),
            discord.SelectOption(label="EE", description="Builds role menus for EE"),
            discord.SelectOption(label="EGR", description="Builds role menus for EGR"),
            discord.SelectOption(label="ME", description="Builds role menus for ME"),
        ]

        select = discord.ui.Select(placeholder="Select an option", max_values=len(options), options=options)

        option_view = View(timeout=None)
        option_view.add_item(select)

        # nested function to allow callback to take the list of selected prefixes as a parameter
        async def callback_helper(interaction):
            await self.rolemenu_callback(interaction, select.values)
            await message.delete()

        select.callback = callback_helper

        await interaction.response.send_message("Select one or more prefixes", view=option_view)
        message = await interaction.original_response()

    @app_commands.command(description="Add a role and have a button for it")
    @app_commands.default_permissions(administrator=True)
    async def create_role_button(self, interaction:discord.Interaction, role_name:str, button_name:str, emoji:str = 'None'):
        """Creates role menus
        Take in user input for what button and role to create
        Check the role given to see if it is a URL
        If the role is a URL dont give the button a callback
        Create the role given (if it doesn't already exist)
        Create the button and put it in a view
        Send the role menu consisting of the view to the user

        EMOJIS: Regular Discord emojis can be entered into the button_name string,
        however emojis created by user need to be entered using the emoji parameter,
        and is added to the beginning of the button
        """

        await interaction.response.defer(ephemeral=True)
        permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, 
                attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, 
                stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)

        # if a user entered a role mention, get the role object + name
        if role_name.startswith("<@&") and role_name.endswith(">"):
            role_name = role_name[3:-1]

            try:
                role = interaction.guild.get_role(int(role_name))
            except ValueError:
                role = None

            if role:
                role_name = role.name

        # create the role if it does not exist
        if not get(interaction.guild.roles, name=role_name):
            role = await interaction.guild.create_role(name=role_name, permissions=permissions)
            role.mentionable = True

        # create the button
        view = View(timeout=None)
        this_button = RoleButton(button_name=button_name, role_name=role_name)
        if emoji != 'None':
            this_button.emoji = emoji
            
        # If there is not a url give it a callback otherwise continue
        if not this_button.url:
            this_button.callback = this_button.on_click
        view.add_item(this_button)

        # send button to user and log command ran
        try:
            await interaction.channel.send(view=view)
        except Exception as e:
            await interaction.channel.send("Emoji doesn't exist, please try again.")
            await log(self.bot, f"{interaction.user} tried creating the '{button_name}' button for role '{role_name}' role in #{interaction.channel} but failed because emoji did not exist")
        else:
            await log(self.bot, f"{interaction.user} created the '{role_name}' role and '{button_name}' button in #{interaction.channel}")
        await interaction.followup.send("Role button was created")
