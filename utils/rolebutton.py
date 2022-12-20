from validators import url

import discord
from discord.ui import Button
from discord.utils import get

class RoleButton(Button):
    """Inherits from discord.ui.Button"""
    def __init__(self, button_name="", role_name="", emoji=""):
        #check if the role_name is a real URL, if so give the button the url and ignore role_name
        if emoji:
            super().emoji=emoji
        if url(role_name):
            super().__init__(label=button_name, url=role_name)
        else:
            super().__init__(label=button_name)
            self.role_name = role_name
        

    async def on_click(self, interaction:discord.Interaction):
        """Gives role to or removes it from user when a role button is clicked
        Gets the role from the server using its name
        Removes the role from the user if they already have it
        Gives the role to the user if they don't already have it
        """
        
        role = get(interaction.guild.roles, name=self.role_name)
        # an interaction.response is necessary for a callback
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"The {role.name} role has been removed from you.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"The {role.name} role has been given to you.", ephemeral=True)
