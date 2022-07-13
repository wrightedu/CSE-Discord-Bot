import discord
from discord.ui import Button
from discord.utils import get

class RoleButton(Button):
    """Inherits from discord.ui.Button
    """
    def __init__(self, button_name="", role_name=""):
        super().__init__(label=button_name)
        self.role_name = role_name

    async def on_click(self, interaction:discord.Interaction):
        # an interaction.response is necessary for a callback
        role = get(interaction.guild.roles, name=self.role_name)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"The {role.name} role has been removed from you.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"The {role.name} role has been given to you.", ephemeral=True)
