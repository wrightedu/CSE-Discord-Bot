import json
import os
import re

import emoji as discord_emoji
import pandas as pd
import validators
from discord.ext import commands
# from discord_components import Button, ButtonStyle, InteractionType
from utils import *

async def setup(bot):
    await bot.add_cog(TestServerManagement(bot))


class TestServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildclasses(self, ctx):
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
        roles_df = pd.read_csv(csv_filepath)

        roles_df = roles_df.dropna(subset=['create_channels'])

        #? TODO Build all channels
        role_names=roles_df["role/link"].to_list()
        class_channels = roles_df["create_channels"].to_list()
        categories = roles_df["text"].to_list()
        long_names = roles_df["long_name"].to_list()

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


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def destroyclasses(self, ctx):
        """Destroy class channels
        ETC
        """

# assuming they are built together and we can trust that, 
# can delete roles and categories together, however,
# when searching categories and roles, they will need to be searched separately
# because the server/guild itself has different amounts to search through