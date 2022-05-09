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
        self.bot = bot

        # Role menu messages
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
        """Creates class channels
        Try to destroy all class channels
        Read in a role csv from a cached file or attachment on command message
        Get confirmation from author
        Create all categories, channels, and roles
        Create role menus
        """

        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'
        # Destroy server before building
        try:
            await self.destroyserver(ctx)
        except FileNotFoundError:
            print('the role_lists directory doesnt exist')
            return

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
        """Destroys all class channels off cached file
        Load in cached classlist csv
        Create list of all channels to be deleted, send to author
        Get confirmation from author
        Delete all listed categories and channels
        Create list of all roles to be deleted, send to author
        Get confirmation from author
        Delete all listed roles
        """

        # Load roles csv

        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        try:
            roles_csvs = pd.read_csv(csv_filepath)
        except FileNotFoundError:
            raise FileNotFoundError

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
        """Creates role menus
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
        """Handles button clicks for role menus
        If button clicked is a role menu message,
        Get the role name from the button label
        Get role from role name
        If role doesn't exist, error
        If role does exist, apply or remove the role to the member who clicked the button
        """
        msg_id = res.message.id
        guild_id = str(res.guild.id)

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
