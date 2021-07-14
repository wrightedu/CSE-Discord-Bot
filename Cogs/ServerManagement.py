import json
import os
import re

import emoji as discord_emoji
import pandas as pd
import validators
from discord.ext import commands
from discord_components import Button, ButtonStyle, InteractionType
from utils import *


def setup(bot):
    bot.add_cog(ServerManagement(bot))


class ServerManagement(commands.Cog):
    def __init__(self, bot):
        """
        Read the role menus file and save it to a variable "role_menus".
        
        Outputs: Message to user confirming that role menu ids have been read
                -If file not found: Message to user stating that an empty rle menue dictionary was made.
                """
        self.bot = bot

        #   Role menu messages
        # Lists of message ids keyed by guild ids
        try:
            with open('role_menus.json', 'r') as f:
                self.role_menus = json.load(f)
                print('loaded role menu message ids from file')
        except FileNotFoundError:
            self.role_menus = {}
            print('empty role menu dict')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildserver(self, ctx):
        """Generate channels and roles based on a csv
        Save the filepath of the roles csv. Call the destroy server method and check to see if there is a csv attatched
        to the message calling the command. If so, delete the existing csv and save the attatched file. Use pandas to
        read the roles csv. Loop through all of the rows in the csv, and if the row is not of type float, add it as a
        catagory to be generated. Send message to user confirming that these catagories are to be made. Loop through the
        rows in the csv, and create a link if there is none already existing. If the role doesn't exist, generate it. 
        Seperate channels to be made from the row and seperate each channel to be made, using commas as a seperator. 
        Create the necessary catagories within the guild and set permissions. For each channel defined within the row, 
        determine whether it will be a text or voice channel and generate. Finally, call the rolemenu method. 

        Args:
            ctx: 
                message (Message): The message sent calling the command. 
                    attachment (List[Attachment]): Any attachment that may be tagged on to the message calling the command
        """
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        # Destroy server before building
        await self.destroyserver(ctx)

        # If csv file attached, overwrite existing csv
        if len(ctx.message.attachments) > 0:
            try:
                os.remove(csv_filepath)
            except FileNotFoundError:
                pass
            await ctx.message.attachments[0].save(csv_filepath)

        # Load roles csv
        roles_csvs = pd.read_csv(csv_filepath)

        # Print list of channels to build
        message = '__**CREATE FOLLOWING CATEGORIES**__\n'
        for _, row in roles_csvs.iterrows():
            if type(row['create_channels']) != float:
                message += f'{row["text"]}\n'
        await ctx.send(message)

        # Get confirmation before building channels
        if not await confirmation(self.bot, ctx, 'build'):
            return

        # Build all channels
        for _, row in roles_csvs.iterrows():
            # If role isn't a link, create role
            if not validators.url(row['role/link']):
                # If role doesn't already exist (due to cross-listing)
                role_exists = any(role.name == row['role/link'] for role in ctx.guild.roles)
                if not role_exists:
                    permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
                    role = await ctx.guild.create_role(name=row['role/link'], permissions=permissions)
                    role.mentionable = True

            # If channels to make
            if type(row['create_channels']) != float:
                channels = row['create_channels'].split(',')
                # Create category and channels
                if len(channels) > 0:
                    # Create category
                    category = await ctx.guild.create_category(row['text'])
                    await category.set_permissions(ctx.guild.default_role, read_messages=False)
                    for role in ctx.guild.roles:
                        if role.name == row['role/link']:
                            await category.set_permissions(role, read_messages=True)

                # Create channels
                for channel in channels:
                    # Create text channel
                    if channel.startswith('#'):
                        text_channel = await category.create_text_channel(channel)
                        await text_channel.edit(topic=row['long_name'])
                    # Create voice channel
                    else:
                        member_count, channel_name = channel.split('#')
                        if member_count == 0:
                            await category.create_voice_channel(channel_name)
                        else:
                            await category.create_voice_channel(channel_name, user_limit=int(member_count))

        # Build role menus
        await self.rolemenu(ctx)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def destroyserver(self, ctx):
        """Systematically delete every role and every channel
        Save the most likely filepath for the roles csv. Load it, and read it using pandas. Create a list
        of the names of catagories to be destroyed by reading the roles csv. Loop through the catagories
        in the guild and see if it is in the csv. If it is, add it to a list of names of catogories to be 
        destroyed. Send a message to user as to which catagories are being destroyed. Use 'confirmation'
        method from utils.py to ensure command is desired, then loop through every channel within every
        catagory and delete them. Read through the roles csv and save to a list 'destroy_role_names'. Loop
        through every role within the guild and check to see if it is in the list of roles to destroy. If
        so, add it to a list of roles to destroy. Confirm that the user wishes to destroy these. Then destroy
        them. 
        
        """
        # Load roles csv
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'
        roles_csvs = pd.read_csv(csv_filepath)

        # = Destroy Categories =

        # List of names of categories to be destroyed, as determined by saved csv
        destroy_category_names = roles_csvs['text'].tolist()

        # Get list of all categories (category objects) to be destroyed and print
        destroy_categories = []
        message = '__**DESTROY FOLLOWING CATEGORIES**__\n'
        for category in ctx.guild.categories:
            if category.name in destroy_category_names:
                message += f'{category.name}\n'
                destroy_categories.append(category)
        await ctx.send(message)

        # Get confirmation before destroying channels
        if len(destroy_categories) and not await confirmation(self.bot, ctx, 'destroy'):
            return

        # Destroy categories and all subchannels
        for category in destroy_categories:
            for channel in category.channels:
                await channel.delete()
            await category.delete()

        # = Destroy Roles =

        # List of names of role to be destroyed, as determined by saved csv
        destroy_role_names = roles_csvs['role/link'].tolist()

        # Get list of all roles (role objects) to be destroyed and print
        destroy_roles = []
        message = '__**DESTROY FOLLOWING ROLES**__\n'
        for role in ctx.guild.roles:
            if role.name in destroy_role_names:
                message += f'{role.mention}\n'
                destroy_roles.append(role)
        await ctx.send(message)

        # Get confirmation before destroying channels
        if len(destroy_roles) and not await confirmation(self.bot, ctx, 'destroy'):
            return

        # Destroy categories and all subchannels
        for role in destroy_roles:
            await role.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rolemenu(self, ctx):
        """Generate a menu of roles for each channel in the server
        Save the most likely filepath of the csv. If a file was already attatched, delete the csv that 
        is already on the operating system and save the attatchment as the new filepath. Read the csv. 
        Use regex to determine what type of type of class (IE: CEG,CS,CEG,etc...) the roles of a row 
        correspond to, and therefore what channel they should be in. If this cannot be found in the csv,
        ask the user for a channel. If this channel exists, save it as the channel name. Add this to the 
        dictionary of channels. Print out a list of all channels and confirm with the user that they are
        to be purged. After receiving confirmation, loop through every channel and call the get_channel_named
        method from utils.py. Create a list of buttons from previous dictionary. Loop through again and
        determine whether the buttons correspond to roles or to url links, and style them accordingly. 
        Shape the button panel into sets of 5x5 grids, with each grid being saved in the menus list. 

        Args:
            CTX:
                message (Message): The message being sent that is calling the command
                    attatchments (List[Attachment]): objects such as files that have been attatched to the message. 
        
        Outputs: 
            -Array of buttons for the role menu.
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
        roles_csv = pd.read_csv(csv_filepath)

        # Determine which channel to send each role menu in
        class_number_regex = '^[a-zA-Z]{2,3} ?\\d{4}'
        menu_roles = {}
        for i, row in roles_csv.iterrows():
            # Get channel name for role button
            channel_name = None
            # If row is for class
            if re.match(class_number_regex, row['text']):
                # Letters at beginning denote category
                text = row['text'].lower().strip()
                category = ''
                for j in range(len(text)):
                    if text[j] not in 'abcdefghijklmnopqrstuvwxyz':
                        category = text[:j]
                        break
                channel_name = f'{category}-class-selection'

            # If can't find channel, ask for it
            while channel_name is None:
                await ctx.send(f'Channel for `{row["text"]}` not found, enter channel to send to')
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if len(msg.channel_mentions):
                    channel_name = msg.channel_mentions[0].name

            # Add role to dictionary entry for channel
            if channel_name not in menu_roles.keys():
                menu_roles[channel_name] = []
            menu_roles[channel_name].append(list(roles_csv.loc[i]))

        # Get confirmation before purging
        channel_names_string = ''
        for channel_name in menu_roles.keys():
            channel_names_string += (await get_channel_named(ctx.guild, channel_name)).mention + '\n'
        await ctx.send(f'The following channels will be **PURGED**!!! Continue?\n{channel_names_string}')
        if not await confirmation(self.bot, ctx, 'purge'):
            await ctx.send('Terminating execution')
            return

        # For each channel, create role menus
        self.role_menus[str(ctx.guild.id)] = []
        for channel_name, roles in menu_roles.items():
            channel = await get_channel_named(ctx.guild, channel_name)

            # Iterate through this channel's roles, creating 1D list of all buttons required
            buttons = []
            for role_data in roles:
                # Data for the current role
                text, emoji_name, role_link, long_name, create_channels = role_data
                emoji_name = str(emoji_name)

                # Get emoji object from current guild if possible
                if emoji_name != 'nan':
                    emoji = await get_emoji_named(ctx.guild, emoji_name)
                    if emoji is None:
                        emoji = discord_emoji.emojize(f':{emoji_name}:', use_aliases=True)
                        if emoji == f':{emoji_name}:':
                            emoji = None
                else:
                    emoji = None

                # If role, make button style gray. If URL, make style URL
                label = f'{text} - {long_name}' if str(long_name) != 'nan' else text
                if not validators.url(role_link):
                    buttons.append(Button(style=ButtonStyle.gray, label=label, emoji=emoji))
                else:
                    buttons.append(Button(style=ButtonStyle.URL, label=label, emoji=emoji, url=role_link))

            # Reshape buttons to sets of max 5x5
            menus = []  # list of 2D grids of buttons
            for i in range(0, len(buttons), 25):
                chunk = buttons[i:i + 25]
                menus.append([chunk[i:i + 5] for i in range(0, len(chunk), 5)])

            # Clear channel
            await channel.purge()

            # Send each role menu
            for menu in menus:
                # Send and save message
                message = await channel.send('‍\u200c', components=menu)  # 0 width joiner in here to send empty message
                self.role_menus[str(ctx.guild.id)].append(message.id)

        # Save new role menu message ids to file
        with open('role_menus.json', 'w') as f:
            json.dump(self.role_menus, f)

    @commands.Cog.listener()
    async def on_button_click(self, res):
        """Add or Remove user from role based on a button click. 
        Save message id and guild id. If the button is in the role menu, load the roles csv, get role name, and loop
        through rows in the csv to see what role matches with the name on the button. Loop through all roles in the
        guild roles to see if any match the role name and save it. If none match, output error message. Otherwise, 
        call get_member method from utils.py. Check to see if the role is already in the user's list of roles. If so, 
        remove the role. If not, add the role. 

        Args:
            res (discord.ext.commands.context.Context): Modified by discord-components and is very similar to 
                                                        ctx in application.
                
        Outputs:
            -Error message to user if the role clicked on does not exist
        """
        msg_id = res.message.id
        guild_id = str(res.guild.id)

        # print(guild_id, self.role_menus.keys(), guild_id in self.role_menus.keys())
        # print(msg_id, self.role_menus[guild_id], msg_id in self.role_menus[guild_id])
        # print(self.role_menus[guild_id])

        # If clicked on role menu
        if guild_id in self.role_menus.keys() and msg_id in self.role_menus[guild_id]:
            # Load roles csv
            roles_csv = pd.read_csv(f'role_lists/roles_{guild_id}.csv')

            # Get role name
            role_name = ''
            for _, row in roles_csv.iterrows():
                if res.component.label in {row['text'], f'{row["text"]} - {row["long_name"]}'}:
                    role_name = row['role/link']

            # Get object for class role
            role = None
            for guild_role in res.guild.roles:
                if guild_role.name == role_name:
                    role = guild_role
                    break

            # If role doesn't exist, error
            if role is None:
                await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'The {role_name} role does not exist, please contact an admin')

            else:
                # Get member object to give role to or take role from
                member = await get_member(res.guild, res.user.id)

                # Assign or remove role
                if role in member.roles:
                    await member.remove_roles(role)
                    await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'Took the {role.name} role!')
                else:
                    await member.add_roles(role)
                    await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'Gave you the {role.name} role!')
