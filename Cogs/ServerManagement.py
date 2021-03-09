import json
import os
from os.path import exists

from discord.ext import commands
from utils import *


def setup(bot):
    bot.add_cog(ServerManagement(bot))


class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(self, 'reaction_roles'):
            self.reaction_roles = {}

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def buildserver(self, ctx):
        guild = ctx.guild
        reaction_roles_filename = f'reaction_roles_{guild.id}.json'

        # If reaction roles specified in attachment
        if len(ctx.message.attachments) > 0:
            try:
                os.remove(reaction_roles_filename)
            except FileNotFoundError:
                pass
            await ctx.message.attachments[0].save(reaction_roles_filename)
            with open(reaction_roles_filename, 'r') as f:
                self.reaction_roles[guild.id] = (guild, json.loads(f.read()))

        # If reaction roles not loaded for this guild, try to load from file
        if ctx.guild.id not in self.reaction_roles.keys():
            print('here')
            # Next try to load from file
            if exists(reaction_roles_filename):
                with open(reaction_roles_filename, 'r') as f:
                    self.reaction_roles[guild.id] = (guild, json.loads(f.read()))

            # Finally give up on loading and terminate command
            else:
                await ctx.send('Reaction roles JSON not found, rerun command with JSON attached')
                await log(self.bot, 'Reaction roles JSON not found, rerun command with JSON attached')
                return

        # If reaction roles JSON found (or attached)
        await log(self.bot, f'BUILDING SERVER {ctx.guild} ({ctx.author})')
        await destroy_server_helper(self.bot, ctx)
        await build_server_helper(self.bot, ctx, self.reaction_roles)
        await log(self.bot, 'Recreating reaction role menus')
        self. reaction_message_ids = await create_role_menu(self.bot, ctx.guild, self.reaction_roles)
        await ctx.send('Done')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def destroyserver(self, ctx):
        await log(self.bot, f'DESTROYING SERVER ({ctx.author})')
        await destroy_server_helper(self.bot, ctx)
        await ctx.send('Done')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rolemenu(self, ctx):
        guild = ctx.guild
        reaction_roles_filename = f'reaction_roles_{guild.id}.json'

        # If reaction roles specified in attachment
        if len(ctx.message.attachments) > 0:
            try:
                os.remove(reaction_roles_filename)
            except FileNotFoundError:
                pass
            await ctx.message.attachments[0].save(reaction_roles_filename)
            with open(reaction_roles_filename, 'r') as f:
                self.reaction_roles[guild.id] = (guild, json.loads(f.read()))

        self.reaction_message_ids = await create_role_menu(self.bot, ctx.guild, self.reaction_roles)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.message_id in self.reaction_message_ids:
                # Get guild
                guild_id = payload.guild_id
                guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)

                # Get guild reaction roles
                guild_reaction_roles = self.reaction_roles[guild_id][1]

                # Find a role corresponding to the emoji name.
                classes = []
                for menu in guild_reaction_roles.keys():
                    for class_name in guild_reaction_roles[menu].keys():
                        if class_name not in ['channel_name', 'clear_channel']:
                            classes.append(guild_reaction_roles[menu][class_name])
                role = None
                for _class in classes:
                    emoji = f':{_class["emoji"]}:'
                    if emoji in str(payload.emoji):
                        role = discord.utils.find(lambda r: r.name == _class['role'].replace(' ', ''), guild.roles)

                # If role found, assign it
                if role is not None:
                    member = await guild.fetch_member(payload.user_id)
                    if not member.bot:  # Error suppression
                        # Get class name from role
                        await member.add_roles(role)
                        await dm(member, f'Welcome to {role}!')
                        await log(self.bot, f'Assigned role {role} to {member}')
        except Exception:
            await log(self.bot, 'Error suppressed, likely due to bot reacting to a role menu')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id not in self.reaction_message_ids:
            return

        # Get guild
        guild_id = payload.guild_id
        guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)

        # Get guild reaction roles
        guild_reaction_roles = self.reaction_roles[guild_id][1]

        # Find a role corresponding to the emoji name.
        classes = []
        for menu in guild_reaction_roles.keys():
            for class_name in guild_reaction_roles[menu].keys():
                if class_name not in ['channel_name', 'clear_channel']:
                    classes.append(guild_reaction_roles[menu][class_name])
        role = None
        for _class in classes:
            emoji = f':{_class["emoji"]}:'
            if emoji in str(payload.emoji):
                role = discord.utils.find(lambda r: r.name == _class['role'].replace(' ', ''), guild.roles)

        # If role found, take it
        if role is not None:
            member = await guild.fetch_member(payload.user_id)
            await member.remove_roles(role)
            await dm(member, f'We\'ve taken you out of {role}')
            await log(self.bot, f'Took role {role} from {member}')
