import json
import os
import re

import emoji as discord_emoji
import pandas as pd
import validators
from discord.ext import commands
from discord.utils import get
# from discord_components import Button, ButtonStyle, InteractionType
from utils.utils import *
from discord.ui import Button, View
from discord import ButtonStyle

from utils.buttons import Button

async def setup(bot):
    await bot.add_cog(TestServerManagement(bot))


class TestServerManagement(commands.Cog):
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
        ETC
        """

        #destroy classes first here
        #check if built before first?

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

        #? TODO Build all channels
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
        
        #TODO: re-evalate permissions?
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
            await category.set_permissions(ctx.guild.default_role, read_messages=False) # sets category to private
            await category.set_permissions(role, read_messages=True) # allow role to see category
            
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
        ETC
        """

        # Load roles csv
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        # If the role_lists directory doesn't exist raise a FileNotFoundError back to the buildserver command
        try:
            courses_df = pd.read_csv(csv_filepath)
        except FileNotFoundError:
            raise FileNotFoundError

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


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildrolemenu(self, ctx):
        """Creates role menus
        #***EDIT????***
        Read in a role csv from a cached file or attachment on command message
        Try to figure out which channels to send each role button in
        For those that can't be determined, ask for user input
        Get confirmation before purging role selection channels
        Create groupings of buttons to fit into a 5x5 grid, row major, left to right
        Send button groups to appropriate channels
        Save button group message ids to self.role_menus and file
        """
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
        role_names=courses_df["role/link"].to_list()
        categories = courses_df["text"].to_list()

        #* Create the course button and link it to the proper class role
        for i in range(len(role_names)):
            # Create buttons
            role_name = role_names[i]



    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildbutton(self, ctx):
        """
        Create buttons, Da
        #? Return a button?
        """

        # # Create label for button
        # label = "help me"
        
        # # Create the button
        # test_but = Button(style=ButtonStyle.gray, label=label)
        
        # # Create a view to add the button to the message
        # this_view = View()
        # this_view.add_item(test_but)
        
        # # Send the message
        # await ctx.send(view=this_view)

        # await self.helloworld(ctx)

        view=Button()
        #view.blurple_button()

        quick_list = ["AHH", "dayn", "brain no work"]
        view.list_test(quick_list)

        # shows button to user
        await ctx.send("This message has buttons!",view=view)

    
    @commands.Cog.listener()
    async def on_button_clic(self, res):
        #await interaction.response.edit_message(content=f"This is an edited button response!")
        print("Hello world!")

    @discord.ui.button(label="Button",style=discord.ButtonStyle.gray)
    async def gray_button(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.response.edit_message(content=f"This is an edited button response!")