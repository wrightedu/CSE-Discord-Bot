import json
import os
import re

import emoji as discord_emoji
import pandas as pd
import validators
from discord.ext import commands
from discord.utils import get
from utils.utils import *
from discord.ui import Button, View
from discord import ButtonStyle
from utils.rolebutton import RoleButton

from utils import *
from discord import app_commands

async def setup(bot):
    await bot.add_cog(ClassManagement(bot))


class ClassManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_category(self, ctx, category_names):
        """ Looks through all categories and verifies if the list of category names is on the server

        Args:
            category_names (List[str]): a list of strings of the category names to delete

        Outputs:
            categories (List[categories]): a list of the verified categories.
        
        """

        # Get list of all categories (category objects) to be destroyed and print
        categories = []
        missing_categories = '__**MISSING FOLLOWING CATEGORIES**__\n'

        for category_name in category_names:
            category = get(ctx.guild.categories, name=category_name)

            # If the category was not found it adds it to the missing_categories message
            if category == None:
                missing_categories += f'{category_name}\n'
            else:
                categories.append(category)

        # only send if there are missing categories
        if not len(categories) == len(category_names):
            await ctx.send(missing_categories)

        return categories

    async def get_roles(self, ctx, role_names):
        """ Looks through all roles and verifies if the list of role names is on the server

        Args:
            role_names (List[str]): a list of strings of the role names to delete

        Outputs:
            roles (List[roles]): a list of the verified roles.

        """

        # Get list of all categories (category objects) to be destroyed and print
        roles = []
        missing_roles = '__**MISSING FOLLOWING ROLES**__\n'

        for role_name in role_names:
            role = get(ctx.guild.roles, name=role_name)

            # If the role was not found it adds it to the missing_roles message
            if role == None:
                missing_roles += f'{role_name}\n'
            else:
                roles.append(role)
        
        # only send if there are missing roles
        if not len(roles) == len(role_names):
            await ctx.send(missing_roles)

        return roles

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildcourses(self, ctx):
        """Create class channels

        Try to destroy old class channels (calls on destroycourses)
        Read in role csv from cached file or from attachment on discord message
        Get confirmation from author
        Create all categories, channels, and roles
        Call command to create role menus
        """

        #destroy classes first here
        await self.destroycourses(ctx)

        # Load roles csv
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        # If csv file attached, overwrite existing csv
        if len(ctx.message.attachments) > 0:
            try:
                os.remove(csv_filepath)
            except FileNotFoundError:
                pass
            await ctx.message.attachments[0].save(csv_filepath)
        
        # Load roles csv
        courses_df = pd.read_csv(csv_filepath)

        courses_df = courses_df.dropna(subset=['create_channels'])

        role_names=courses_df["role/link"].to_list()
        class_channels = courses_df["create_channels"].to_list()
        categories = courses_df["text"].to_list()
        long_names = courses_df["long_name"].to_list()

        # Print to user list of channels to build
        message = '__**CREATE FOLLOWING CATEGORIES**__\n'
        for category_name in categories:
            message += f'{category_name}\n'
        await ctx.send(message)

        # Get confirmation before building channels
        if not await confirmation(self.bot, ctx, 'build'):
            return
        
        #TODO: for future, re-evalate what permissions are needed?
        permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, 
                attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, 
                stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
        
        for i in range(len(role_names)):
            # Create roles
            role_name = role_names[i]
            role = await ctx.guild.create_role(name=role_name, permissions=permissions)
            role.mentionable = True
            
            # Create category
            category_name = categories[i]
            category = await ctx.guild.create_category(category_name)
            await category.set_permissions(ctx.guild.default_role, read_messages=False)      # sets category to private
            await category.set_permissions(role, read_messages=True)        # allow role to see category
            
            # Create channels
            channels = class_channels[i].split(",")

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
        await ctx.send('***CATEGORIES AND ROLES HAVE BEEN BUILT***')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def destroycourses(self, ctx):
        """Destroy course channels

        Try loading in cached classlist csv
        Create list of all channels to be deleted, send to author
        Get confirmation from author
        Delete all listed categories and channels
        Create list of all roles to be deleted, send to author
        Get confirmation from author
        Delete all listed roles
        """

        # Load roles csv
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        # If the role_lists directory doesn't exist raise a FileNotFoundError back to the buildserver command
        try:
            courses_df = pd.read_csv(csv_filepath)
        except FileNotFoundError:
            raise FileNotFoundError

        # drop cross-listed courses (and other roles if on the file)
        courses_df = courses_df.dropna(subset=['create_channels'])

        # List of names of categories to be destroyed, as determined by saved csv
        destroy_category_names = courses_df['text'].tolist()
        destroy_categories = await self.get_category(ctx, destroy_category_names)

        # List of names of role to be destroyed, as determined by saved csv
        destroy_role_names = courses_df['role/link'].tolist()
        destroy_roles = await self.get_roles(ctx, destroy_role_names)
        

        message = '__**DESTROY FOLLOWING CATEGORIES**__\n'
        if len(destroy_categories):
            for category in destroy_categories:
                message += f'{category.name}\n'
        else:
            message += f'NO CATEGORIES FOUND\n'
        
        message += '__**DESTROY FOLLOWING ROLES**__\n'
        if len(destroy_roles):
            for role in destroy_roles:
                message += f'{role.mention}\n'
        else:
            message += f'NO ROLES FOUND\n'
        
        await ctx.send(message)
        if not await confirmation(self.bot, ctx, 'destroy'):
            return
        
        # Destroy categories and all subchannels
        for category in destroy_categories:
            for channel in category.channels:
                await channel.delete()
            await category.delete()
        
        for role in destroy_roles:
            await role.delete()

        await ctx.send('***CATEGORIES AND ROLES HAVE BEEN DESTROYED***')

    #TODO: Have the role menus built into their proper channels
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildrolemenu(self, ctx):
        """Creates role menus

        find csv and extracts columns needed through a panda dataframe
        create the buttons and put them in a view
        aka the role menu, and send to user
        """

        # finds csv and extracts appropriate columns using a dataframe
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'
        courses_df = pd.read_csv(csv_filepath)
        short_names = courses_df["text"].to_list()
        long_names = courses_df["long_name"].to_list()
        role_names=courses_df["role/link"].to_list()

        # adds RoleButtons to a view with custom attributes and sends it to chat
        # make sure to give the timeout None in order to keep the buttons working for all semester
        view = View(timeout=None)           # a visual discord container for graphical components
        for i in range(len(role_names)):
            if i % 25 == 0 and i != 0:          # limit of 25 components per view
                await ctx.send(view=view)
                view=View(timeout=None)
            this_button = RoleButton(button_name=f"{short_names[i]} - {long_names[i]}", role_name=role_names[i])
            this_button.callback = this_button.on_click
            view.add_item(this_button)

        await ctx.send(view=view)

#TODO: slash command for other roles, see github #117 comment on 7/25 for details

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def otherroles(self, ctx):
        """Creates a button for other roles

        take in user input for what button and role to create
        create the role given (if it doesn't already exist)
        create the button and put it in a view
        aka the role menu, and send to user
        """

        permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, 
                attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, 
                stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)

        # get user input for what the role should be
        await ctx.send(f'What role would you like to create?')
        role = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
        
        # create the role
        #TODO: check to see if the role already exists
        the_role = await ctx.guild.create_role(name=role.content, permissions=permissions)
        the_role.mentionable = True

        # ask name for the button
        await ctx.send(f'What should the button be called?')
        button = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
        view = View(timeout=None)       # keeps buttons from disappearing

        # create button
        this_button = RoleButton(button_name=button.content, role_name=role.content)
        this_button.callback = this_button.on_click
        view.add_item(this_button)

        # send to user
        await ctx.send(view=view)


    # @app_commands.command(description="add another role")
    # @app_commands.default_permissions(administrator=True)
    # async def createrolebutton(self, ctx, interaction:discord.Interaction):
    #     """An example slash command
    #     This command can only be executed by those with admin permissions.
        
    #     Outputs:
    #         Message to user confirming execution.
    #     """

    #     """Creates role menus

    #     take in user input for what button and role to create
    #     create the role given (if it doesn't already exist)
    #     create the button and put it in a view
    #     aka the role menu, and send to user
    #     """

    #     permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, 
    #             attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, 
    #             stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)

    #     # get user input for what the role should be
    #     # await ctx.send(f'What role would you like to create?')
    #     role = "rolling"
        
    #     # create the role
    #     #TODO: check to see if the role already exists
    #     the_role = await ctx.guild.create_role(name=role.content, permissions=permissions)
    #     the_role.mentionable = True

    #     # ask name for the button
    #     await ctx.send(f'What should the button be called?')
    #     button = "role - rolling"
    #     view = View(timeout=None)       # keeps buttons from disappearing

    #     # create button
    #     this_button = RoleButton(button_name=button.content, role_name=role.content)
    #     this_button.callback = this_button.on_click
    #     view.add_item(this_button)

    #     # send to user
    #     return await ctx.send(view=view)
    #     #return await interaction.response.send_message("Hiiiiiiii, CogManage")