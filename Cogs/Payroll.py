import os
import sys
import asyncio
import sqlite3
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks


TEST_GUILD_ID = 808423775048564807
PAYROLL_CHANNEL_ID = 1562188681824047266

EMPLOYEE_ROLE_ID = 1172287866882244689
SUPERVISOR_ROLE_ID = 808425691795947610

FIRST_TIMESHEET_FRIDAY = date(2026, 10, 23)
REMINDER_HOURS = (9, 12, 15)
SUPERVISOR_REMINDER_HOURS = (9, 12, 13)
TIMEZONE = ZoneInfo("America/New_York")
PAYROLL_DB = "payroll_reminders.db"

SUPERVISOR_URL = "https://wingsexpress.wright.edu/EmployeeSelfService/"


def is_timesheet_friday(check_date):
    """Return True for alternating timesheet Fridays."""

    days_since = (
        check_date - FIRST_TIMESHEET_FRIDAY
    ).days

    return (
        days_since >= 0
        and check_date.weekday() == 4
        and days_since % 14 == 0
    )


def is_supervisor_monday(check_date):
    """Return True for Mondays after timesheet Fridays."""

    previous_friday = check_date - timedelta(days=3)

    return (
        check_date.weekday() == 0
        and is_timesheet_friday(previous_friday)
    )
    
class Payroll(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Create the reminder tracking table
        with sqlite3.connect(PAYROLL_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_reminders (
                    reminder_key TEXT PRIMARY KEY
                )
            """)

        # Start both automatic reminder schedulers
        self.reminder_loop.start()
        self.supervisor_reminder_loop.start()

    def cog_unload(self):
        """Stop background tasks when the Cog unloads."""

        self.reminder_loop.cancel()
        self.supervisor_reminder_loop.cancel()

    # Slash command group
    payroll = app_commands.Group(
        name="payroll",
        description="Payroll related commands"
    )

    def already_sent(self, reminder_key):
        """Check whether a reminder has already been sent."""

        with sqlite3.connect(PAYROLL_DB) as conn:
            result = conn.execute(
                """
                SELECT 1
                FROM sent_reminders
                WHERE reminder_key = ?
                """,
                (reminder_key,)
            ).fetchone()

        return result is not None

    def mark_sent(self, reminder_key):
        """Record a successfully sent reminder."""

        with sqlite3.connect(PAYROLL_DB) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sent_reminders
                (reminder_key)
                VALUES (?)
                """,
                (reminder_key,)
            )

    def make_reminder_embed(self, hour, testing=False):

        if hour == 9:
            message = (
                "Good morning! Just a friendly reminder "
                "to submit your timesheet for this week."
            )

        elif hour == 12:
            message = (
                "Good afternoon! Hope you enjoyed your lunch! "
                "Just a friendly reminder to submit your "
                "timesheet for this week."
            )

        else:
            message = (
                "Only 2 hours left to submit your timesheet! "
                "Please submit it before the deadline "
                "so you can be paid on time!"
            )

        title = "Timesheet Submission Reminder"

        if testing:
            title += " (TESTING)"

        embed = discord.Embed(
            title=title,
            description=(
                f"{message}\n\n"
                "**Employee timesheets are due "
                "by 5:00 PM today!**"
            ),
            color=discord.Color.blue()
        )

        if testing:
            embed.set_footer(
                text="Testing message - no action required"
            )

        return embed

    def make_supervisor_reminder_embed(self, hour, testing=False):
        if hour == 9:
            message = "Good morning! Please review and approve your employees' timesheets."
        elif hour == 12:
            message = "Good afternoon! Please check for any outstanding employee timesheets that still need your approval."
        else:
            message = "Only 1 hour left to approve employee timesheets! Please complete all approvals before the deadline."

        title = "Supervisor Timesheet Approval Reminder"
        if testing:
            title += " (TESTING)"

        embed = discord.Embed(
            title=title,
            description=f"{message}\n\n**Supervisor approvals are due by 2:00 PM today!**",
            color=discord.Color.orange()
        )

    # Add the supervisor approval link
        embed.add_field(
            name="Supervisor Approval Portal",
            value=f"[Open Employee Self-Service]({SUPERVISOR_URL})",
            inline=False
        )

        if testing:
            embed.set_footer(text="Testing message - no action required")

        return embed

    @tasks.loop(minutes=1)
    async def reminder_loop(self):

        now = datetime.now(TIMEZONE)

        if not is_timesheet_friday(now.date()):
            return

        if now.hour not in REMINDER_HOURS:
            return

        if now.minute != 0:
            return

        reminder_key = (
            f"employee-{now.date().isoformat()}-{now.hour:02d}"
        )

        if self.already_sent(reminder_key):
            return

        guild = self.bot.get_guild(TEST_GUILD_ID)

        if guild is None:
            print("Payroll: testing server not found")
            return

        channel = guild.get_channel(PAYROLL_CHANNEL_ID)

        if channel is None:
            print("Payroll: testing channel not found")
            return

        role = guild.get_role(EMPLOYEE_ROLE_ID)

        if role is None:
            print("Payroll: employee role not found")
            return

        embed = self.make_reminder_embed(now.hour)

        try:
            await channel.send(
                content=role.mention,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    everyone=False,
                    users=False,
                    roles=[role]
                )
            )

            self.mark_sent(reminder_key)

            print(
                f"Payroll: sent employee reminder "
                f"{reminder_key}"
            )

        except discord.DiscordException as error:
            print(
                f"Payroll: employee reminder failed: {error}"
            )

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def supervisor_reminder_loop(self):

        now = datetime.now(TIMEZONE)

        if not is_supervisor_monday(now.date()):
            return

        if now.hour not in SUPERVISOR_REMINDER_HOURS:
            return

        if now.minute != 0:
            return

        reminder_key = (
            f"supervisor-{now.date().isoformat()}-{now.hour:02d}"
        )

        if self.already_sent(reminder_key):
            return

        guild = self.bot.get_guild(TEST_GUILD_ID)

        if guild is None:
            print("Payroll: testing server not found")
            return

        channel = guild.get_channel(PAYROLL_CHANNEL_ID)

        if channel is None:
            print("Payroll: testing channel not found")
            return

        role = guild.get_role(SUPERVISOR_ROLE_ID)

        if role is None:
            print("Payroll: supervisor role not found")
            return

        embed = self.make_supervisor_reminder_embed(
            now.hour
        )

        try:
            await channel.send(
                content=role.mention,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    everyone=False,
                    users=False,
                    roles=[role]
                )
            )

            self.mark_sent(reminder_key)

            print(
                f"Payroll: sent supervisor reminder "
                f"{reminder_key}"
            )

        except discord.DiscordException as error:
            print(
                f"Payroll: supervisor reminder failed: {error}"
            )

    @supervisor_reminder_loop.before_loop
    async def before_supervisor_reminder_loop(self):
        await self.bot.wait_until_ready()

    @payroll.command(
        name="test-system",
        description="Test the payroll reminder system"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def payroll_test(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.guild_id != TEST_GUILD_ID
            or interaction.channel_id != PAYROLL_CHANNEL_ID
        ):
            await interaction.response.send_message(
                "This command can only be used in the "
                "testing server and channel.",
                ephemeral=True
            )
            return

        embed = self.make_reminder_embed(
            9,
            testing=True
        )

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )


    @payroll.command(
        name="test-ping",
        description="Test the employee payroll role ping"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def payroll_test_ping(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.guild_id != TEST_GUILD_ID
            or interaction.channel_id != PAYROLL_CHANNEL_ID
        ):
            await interaction.response.send_message(
                "This command can only be used in the "
                "testing server and channel.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            EMPLOYEE_ROLE_ID
        )

        if role is None:
            await interaction.response.send_message(
                "Employee role not found.",
                ephemeral=True
            )
            return

        embed = self.make_reminder_embed(
            15,
            testing=True
        )

        await interaction.response.send_message(
            content=role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=False,
                roles=[role]
            )
        )

    @payroll.command(
        name="test-supervisor-ping",
        description="Test the supervisor approval reminder"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def payroll_test_supervisor(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.guild_id != TEST_GUILD_ID
            or interaction.channel_id != PAYROLL_CHANNEL_ID
        ):
            await interaction.response.send_message(
                "This command can only be used in the "
                "testing server and channel.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(
            SUPERVISOR_ROLE_ID
        )

        if role is None:
            await interaction.response.send_message(
                "Supervisor role not found.",
                ephemeral=True
            )
            return

        embed = self.make_supervisor_reminder_embed(
            13,
            testing=True
        )

        await interaction.response.send_message(
            content=role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=False,
                roles=[role]
            )
        )
        
async def setup(bot):
    await bot.add_cog(Payroll(bot))
    
    async def sync_payroll_commands():
        await bot.wait_until_ready()
        
        test_guild = discord.Object(id=TEST_GUILD_ID)
        
        try:
            bot.tree.copy_global_to(guild=test_guild)
            await bot.tree.sync(guild=test_guild)
            
        except discord.DiscordException as error:
            print(f"Failed to sync payroll commands: {error}")
            
        bot.loop.create_task(sync_payroll_commands())