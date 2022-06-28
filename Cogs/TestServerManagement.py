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
    async def createClasses(self, ctx):
        """Create class channels
        ETC
        """

        #destroy classes first here
        #check if built before first?

        csv_filepath = f'role_lists/roles_{ctx.guild.id}.csv'

        # If csv file attached, overwrite existing csv
        if len(ctx.message.attachments) > 0:
            try:
                os.remove(csv_filepath)
            except FileNotFoundError:
                pass
            await ctx.message.attachments[0].save(csv_filepath)
        
        # Load roles csv
        roles_csvs = pd.read_csv(csv_filepath)

        # Build all channels
        role_names = roles_csvs['text'].unique().tolist() # check if breaks
        for name in role_names:
            #TODO: re-evalate permissions?
            permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, 
                    attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, 
                    stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
            role = await ctx.guild.create_role(name=name, permissions=permissions)
            role.mentionable = True

    
        # Just have a CS, CEG, EE array or something,
        # if it has that in front of it, delete the role
        # helps deal with persistent roles???