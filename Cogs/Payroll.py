import os

import sqlite3
from datetime import date, datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

# Testing server configuration
TEST_GUILD_ID = 808423775048564807
PAYROLL_CHANNEL_ID = 1562188681824047266
EMPLOYEE_ROLE_ID = 1172287866882244689

# Timesheet schedule
FIRST_TIMESHEET_FRIDAY = date(2026, 10, 23)
REMINDER_HOURS = (9, 12, 15)
TIMEZONE = ZoneInfo("America/New_York")

PAYROLL_DB = "payroll_reminders.db"

# Utility function to check if a given date is a timesheet Friday
def is_timesheet_friday(check_date):
    days_since = (check_date - FIRST_TIMESHEET_FRIDAY).days

    return (
        days_since >= 0
        and check_date.weekday() == 4
        and days_since % 14 == 0
    )

# Payroll Cog 
class Payroll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with sqlite3.connect(PAYROLL_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_reminders (
                    reminder_key TEXT PRIMARY KEY
                )
            """)

        self.reminder_loop.start()

    # Cleanup when the cog is unloaded
    def cog_unload(self):
        self.reminder_loop.cancel()

    payroll = app_commands.Group(
        name="payroll",
        description="Payroll related commands"
    )

    # Check if a reminder has already been sent for a specific hour
    def already_sent(self, reminder_key):
        with sqlite3.connect(PAYROLL_DB) as conn:
            result = conn.execute(
                "SELECT 1 FROM sent_reminders WHERE reminder_key = ?",
                (reminder_key,)
            ).fetchone()

        return result is not None

    # Mark a reminder as sent for a specific hour
    def mark_sent(self, reminder_key):
        with sqlite3.connect(PAYROLL_DB) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sent_reminders VALUES (?)",
                (reminder_key,)
            )

    # Create a reminder embed based on the hour of the day
    def make_reminder_embed(self, hour, testing=False):
        # 9 am
        if hour == 9:
            title = "Timesheet Submission Reminder"
            message = (
                "Good morning! Just a friendly reminder to submit "
                "your timesheet for this week."
            )

        # 12 pm (noon)
        elif hour == 12:
            title = "Timesheet Submission Reminder"
            message = (
                "Good afternoon! Hope you enjoyed your lunch! "
                "Just a friendly reminder to submit your timesheet."
            )

        # 3 pm
        else:
            title = "Timesheet Submission Reminder"
            message = (
                "Only 2 hours left to submit your timesheet! "
                "Please submit it before the deadline so you can "
                "be paid on time!"
            )

        # Add a testing note to the title if this is a test message
        if testing:
            title += " (TESTING)"

        embed = discord.Embed(
            title=title,
            description=(
                f"{message}\n\n"
                "**Employee timesheets are due by 5:00 PM today!**"
            ),
            color=discord.Color.blue()
        )

        if testing:
            embed.set_footer(
                text="Testing message - no action required"
            )

        return embed

    # Background task that runs every minute to check if a reminder should be sent
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
            print(f"Payroll: sent reminder for {reminder_key}")

        except discord.DiscordException as error:
            print(f"Payroll: failed to send reminder: {error}")

    # Before the reminder loop starts, wait until the bot is ready
    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    # Slash command to test the payroll reminder system
    @payroll.command(
        name="test-system",
        description="Test the payroll reminder system"
    )

    @app_commands.checks.has_permissions(administrator=True)
    async def payroll_test(self, interaction: discord.Interaction):
        if (
            interaction.guild_id != TEST_GUILD_ID
            or interaction.channel_id != PAYROLL_CHANNEL_ID
        ):
            await interaction.response.send_message(
                "This command can only be used in the testing server and channel.",
                ephemeral=True
            )
            return

        embed = self.make_reminder_embed(9, testing=True)

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )
    
    # Slash command to test the payroll reminder ping system
    @payroll.command(
        name="test-ping",
        description="Test the payroll reminder ping system"
    )
    
    @app_commands.checks.has_permissions(administrator=True)
    async def payroll_test_ping(self, interaction: discord.Interaction):
        if (
            interaction.guild_id != TEST_GUILD_ID
            or interaction.channel_id != PAYROLL_CHANNEL_ID
        ):
            await interaction.response.send_message(
                "This command can only be used in the testing server and channel.",
                ephemeral=True
            )
            return
        
        role = interaction.guild.get_role(EMPLOYEE_ROLE_ID)
        
        if role is None:
            await interaction.response.send_message(
                "Employee role not found.",
                ephemeral=True
            )
            return
        
        embed = self.make_reminder_embed(15, testing=True)
        
        await interaction.response.send_message(
            content=role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=False,
                roles=[role]
            )
        )

# Setup function to add the Payroll cog to the bot
async def setup(bot):
    await bot.add_cog(Payroll(bot))

    # Temporary testing-server slash command sync
    test_guild = discord.Object(id=TEST_GUILD_ID)

    bot.tree.copy_global_to(guild=test_guild)
    synced = await bot.tree.sync(guild=test_guild)

    print(
        f"Synced {len(synced)} commands "
        f"to testing server {TEST_GUILD_ID}"
    )