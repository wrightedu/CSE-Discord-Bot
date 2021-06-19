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
        pass

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
                print(class_role)
                print(member.roles)
                if class_role in member.roles:
                    await member.remove_roles(class_role)
                    await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'Took the {class_role.name} role!')
                else:
                    await member.add_roles(class_role)
                    await res.respond(type=InteractionType.ChannelMessageWithSource, content=f'Gave you the {class_role.name} role!')
