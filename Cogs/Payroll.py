import os

import discord
from discord import app_commands
from discord.ext import commands

PAYROLL_CHANNEL_ID = 1562188681824047266

class Payroll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    payroll = app_commands.Group(
        name="payroll",
        description="Payroll reminders and commands"
    )
    
    @payroll.command(
        name="test",
        description="Send a test payroll reminder"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def payroll_tetst(self, interation: discord.Interaction):
        if interation.channel.id != PAYROLL_CHANNEL_ID:
            await interation.response.send_message(
                "This command can only be used in the payroll channel.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="Timesheet Reminder (TEST)",
            description=(
                "Please remember to submit your timesheets for this week. "
                "If you have already submitted your timesheet, please disregard this message."
            ),
            color=discord.Color.blue()
        )
        
        embed.set_footer(text="This is a test message. No action is required.")
        
        await interation.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )
        
async def setup(bot):
    await bot.add_cog(Payroll(bot))
    
    test_guild = discord.Object(id=808423775048564807)
    
    bot.tree.copy_global_to(guild=test_guild)
    synced = await bot.tree.sync(guild=test_guild)
    
    print(f"Synced {len(synced)} commands to testing server")