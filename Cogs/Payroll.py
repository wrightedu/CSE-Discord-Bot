import discord
from discord import app_commands
from discord.ext import commands

TEST_GUILD_ID = 808423775048564807
PAYROLL_CHANNEL_ID = 1562188681824047266
EMPLOYEE_ROLE_ID = 1172287866882244689

class TimesheetView(discord.ui.View):
    """
    Display buttons for employee timesheet confirmation.

    Attributes:
        cog: The Payroll cog instance.
        employee_id (int): Discord ID of the employee.
        timeout (None): Buttons do not expire automatically.
    """

    def __init__(self, cog, employee_id):
        """
        Initialize the employee confirmation buttons.

        Args:
            cog (Payroll): Payroll cog instance.
            employee_id (int): Employee Discord user ID.
        """
        super().__init__(timeout=None)
        self.cog = cog
        self.employee_id = employee_id

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        custom_id="payroll:employee:yes"
    )
    async def yes_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user.id != self.employee_id:
            await interaction.response.send_message(
                "This reminder is not assigned to you.",
                ephemeral=True
            )
            return

        self.cog.employee_confirmations[self.employee_id] = True

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="✅ Timesheet submission confirmed!",
            view=self
        )

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        custom_id="payroll:employee:no"
    )
    async def no_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.employee_id:
            await interaction.response.send_message(
                "This reminder is not assigned to you.",
                ephemeral=True
            )
            return

        self.cog.employee_confirmations[self.employee_id] = False

        await interaction.response.send_message(
            "Thanks! I'll remind you again until you submit it.",
            ephemeral=True
        )


class Payroll(commands.Cog):
    """
    Manage employee timesheet reminders and confirmations.

    Attributes:
        bot (commands.Bot): Discord bot instance.
        employee_confirmations (dict): Maps employee IDs
            to their timesheet confirmation status.
    """

    def __init__(self, bot):
        """
        Initialize the Payroll cog.

        Args:
            bot (commands.Bot): Discord bot instance.
        """
        self.bot = bot
        self.employee_confirmations = {}

    payroll = app_commands.Group(
        name="payroll",
        description="Payroll reminder commands"
    )

    @payroll.command(
        name="test-dm",
        description="Send yourself a test timesheet reminder"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def test_dm(self, interaction: discord.Interaction):
        """
        Send a test reminder to the command user.

        Args:
            interaction (discord.Interaction): Slash command
                interaction from the testing server.

        Side Effects:
            Sends a DM with confirmation buttons.
        """
        if (
            interaction.guild_id != TEST_GUILD_ID
            or interaction.channel_id != PAYROLL_CHANNEL_ID
        ):
            await interaction.response.send_message(
                "Use this command in the payroll testing channel.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        view = TimesheetView(self, interaction.user.id)

        try:
            await interaction.user.send(
                "Have you submitted your timesheet?",
                view=view
            )

            await interaction.followup.send(
                "Test timesheet reminder sent to your DMs!",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send you a DM. Check your privacy settings.",
                ephemeral=True
            )


async def setup(bot):
    """
    Register the Payroll cog with the Discord bot.

    Args:
        bot (commands.Bot): Discord bot instance.

    Side Effects:
        Adds the Payroll cog to the bot.
    """
    await bot.add_cog(Payroll(bot))
