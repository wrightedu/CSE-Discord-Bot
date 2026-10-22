import discord
from discord import app_commands
from discord.ext import commands, tasks

from datetime import date, datetime
from zoneinfo import ZoneInfo

# Discord configuration
TEST_GUILD_ID = 808423775048564807
PAYROLL_CHANNEL_ID = 1562188681824047266
EMPLOYEE_ROLE_ID = 1172287866882244689

# Payroll schedule
FIRST_TIMESHEET_FRIDAY = date(2026, 10, 23)
TIMEZONE = ZoneInfo("America/New_York")

ENABLE_AUTOMATIC_REMINDERS = False

EMPLOYEE_REMINDER_START = 9
EMPLOYEE_REMINDER_END = 16


class TimesheetView(discord.ui.View):
    """
    Display buttons for employee timesheet confirmation.

    Attributes:
        cog (Payroll): Payroll cog instance.
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
        """
        Confirm that an employee submitted their timesheet.

        Args:
            interaction (discord.Interaction): Button interaction.
            button (discord.ui.Button): Yes button.

        Side Effects:
            Records confirmation and disables the buttons.
        """
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
        """
        Record that an employee has not submitted a timesheet.

        Args:
            interaction (discord.Interaction): Button interaction.
            button (discord.ui.Button): No button.

        Side Effects:
            Keeps the employee marked as unconfirmed.
        """
        if interaction.user.id != self.employee_id:
            await interaction.response.send_message(
                "This reminder is not assigned to you.",
                ephemeral=True
            )
            return

        # Never undo an existing Yes confirmation.
        if self.cog.employee_confirmations.get(self.employee_id):
            await interaction.response.send_message(
                "Your timesheet is already confirmed.",
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
        employee_confirmations (dict): Tracks employee
            timesheet submission confirmations.
        sent_reminders (set): Tracks hourly reminders sent
            during the current bot session.
    """

    def __init__(self, bot):
        """
        Initialize the Payroll cog and reminder tracking.

        Args:
            bot (commands.Bot): Discord bot instance.
        """
        self.bot = bot

        self.employee_confirmations = {}
        self.sent_reminders = set()

        self.employee_reminder_loop.start()

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
        Send a test timesheet reminder to the command user.

        Args:
            interaction (discord.Interaction): Slash command
                interaction from the testing server.

        Side Effects:
            Sends a private Discord message with buttons.
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
                "I couldn't send you a DM. "
                "Check your privacy settings.",
                ephemeral=True
            )

        except discord.HTTPException as error:
            await interaction.followup.send(
                f"Failed to send test DM: {error}",
                ephemeral=True
            )

    @tasks.loop(minutes=1)
    async def employee_reminder_loop(self):
        """
        Send hourly timesheet reminders to unconfirmed employees.

        Checks the biweekly payroll schedule and sends DMs
        only to employees who have not confirmed submission.

        Side Effects:
            Sends Discord DMs and stores reminder identifiers
            in memory to prevent duplicate hourly messages.
        """
        if not ENABLE_AUTOMATIC_REMINDERS:
            return

        now = datetime.now(TIMEZONE)

        # Check for scheduled biweekly timesheet Fridays.
        days_since = (
            now.date() - FIRST_TIMESHEET_FRIDAY
        ).days

        if (
            days_since < 0
            or now.weekday() != 4
            or days_since % 14 != 0
        ):
            return

        # Only send reminders during scheduled hours.
        if not (
            EMPLOYEE_REMINDER_START
            <= now.hour
            < EMPLOYEE_REMINDER_END
        ):
            return

        if now.minute != 0:
            return

        guild = self.bot.get_guild(TEST_GUILD_ID)

        if guild is None:
            return

        role = guild.get_role(EMPLOYEE_ROLE_ID)

        if role is None:
            return

        for member in role.members:

            if member.bot:
                continue

            # Stop reminders once an employee confirms Yes.
            if self.employee_confirmations.get(member.id, False):
                continue

            reminder_key = (
                now.date().isoformat(),
                now.hour,
                member.id
            )

            if reminder_key in self.sent_reminders:
                continue

            view = TimesheetView(self, member.id)

            try:
                await member.send(
                    "⏰ Timesheet Reminder\n\n"
                    "Have you submitted your timesheet?",
                    view=view
                )

                self.sent_reminders.add(reminder_key)

            except discord.Forbidden:
                print(
                    f"Payroll: Could not DM employee {member.id}"
                )

            except discord.HTTPException as error:
                print(
                    f"Payroll: DM failed for {member.id}: {error}"
                )

    @employee_reminder_loop.before_loop
    async def before_employee_reminder_loop(self):
        """
        Wait until the Discord bot is ready.

        Side Effects:
            Delays the scheduler until Discord is connected.
        """
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """
        Stop the employee reminder scheduler.

        Side Effects:
            Cancels the background task when the cog unloads.
        """
        self.employee_reminder_loop.cancel()


async def setup(bot):
    """
    Register the Payroll cog with the Discord bot.

    Args:
        bot (commands.Bot): Discord bot instance.

    Side Effects:
        Adds the Payroll cog to the bot.
    """
    await bot.add_cog(Payroll(bot))