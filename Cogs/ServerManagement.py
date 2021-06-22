import os

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
        self.role_menus = {}

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildserver(self, ctx):
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
                permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
                await ctx.guild.create_role(name=row['role/link'], permissions=permissions)

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

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def destroyserver(self, ctx):
        # Load roles csv
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'
        roles_csvs = pd.read_csv(csv_filepath)

        # = Destroy Categories =

        # List of names of categories to be destroyed, as determined by saved csv
        destroy_category_names = roles_csvs.iloc[:, 0].tolist()

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
        destroy_role_names = roles_csvs.iloc[:, 2].tolist()

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
    async def rolemenu(self, ctx, title, *args):
        if len(args) > 25:
            return

        buttons = [[Button(style=ButtonStyle.gray, label=j) for j in args[i:i + 5]] for i in range(0, len(args), 5)]
        message = await ctx.channel.send(f'**{title}**', components=buttons)
        if ctx.guild.id not in self.role_menus.keys():
            self.role_menus[ctx.guild.id] = []
        self.role_menus[ctx.guild.id].append(message.id)

    @commands.Cog.listener()
    async def on_button_click(self, res):
        msg_id = res.message.id
        guild_id = res.guild.id

        # If clicked on role menu
        if guild_id in self.role_menus.keys() and msg_id in self.role_menus[guild_id]:
            # Get object for class role
            class_role = None
            class_role_name = res.component.label
            for role in res.guild.roles:
                if role.name == class_role_name:
                    class_role = role
                    break

            # If role doesn't exist, error
            if class_role is None:
                await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'The {class_role_name} role does not exist, please contact an admin')

            else:
                # Get member object to give role to or take role from
                member = await get_member(res.guild, res.user.id)

                # Assign or remove role
                if class_role in member.roles:
                    await member.remove_roles(class_role)
                    await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'Took the {class_role.name} role!')
                else:
                    await member.add_roles(class_role)
                    await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'Gave you the {class_role.name} role!')
