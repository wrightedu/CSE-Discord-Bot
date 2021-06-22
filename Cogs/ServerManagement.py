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

        self.roles_csvs = {}

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildserver(self, ctx):
        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        # If csv file attached, overwrite existing csv
        if len(ctx.message.attachments) > 0:
            try:
                os.remove(csv_filepath)
            except FileNotFoundError:
                pass
            await ctx.message.attachments[0].save(csv_filepath)

        # Load roles csv
        self.roles_csvs[str(ctx.guild.id)] = pd.read_csv(csv_filepath)

        # TODO: destroy server first
        # Print list of channels to build
        message = '__**CREATE FOLLOWING CATEGORIES**__\n'
        for i, row in self.roles_csvs[str(ctx.guild.id)].iterrows():
            if type(row['create_channels']) != float:
                message += f'{row["text"]}\n'
        await ctx.send(message)

        # Build all channels
        if not await confirmation(self.bot, ctx, 'build'):
            return

        for i, row in self.roles_csvs[str(ctx.guild.id)].iterrows():
            # If role isn't a link, create role
            if not validators.url(row['role/link']):
                permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
                await ctx.guild.create_role(name=row['text'], permissions=permissions)

            # If channels to make
            if type(row['create_channels']) != float:
                channels = row['create_channels'].split(',')
                # Create category and channels
                if len(channels) > 0:
                    # Create category
                    category = await ctx.guild.create_category(row['text'])
                    await category.set_permissions(ctx.guild.default_role, read_messages=False)

                    # Create channels
                    for channel in channels:
                        # Create text channel
                        if channel.startswith('#'):
                            text_channel = await category.create_text_channel(row['text'])
                            await text_channel.edit(topic=row['long_name'])
                        # Create TA voice channel
                        elif channel.startswith('TA'):
                            await category.create_voice_channel(channel, user_limit=2)
                        # Create normal voice channel
                        else:
                            await category.create_voice_channel(channel)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def destroyserver(self, ctx):
        # Destroy specific class(es) based on regex?
        pass

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
