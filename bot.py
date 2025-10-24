#!/usr/bin/env python3
import os
from sys import argv
from time import perf_counter

import aiofiles
import discord
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger

from utils.logger import enable_discord_logging, initialize_logger, enable_cli_logging

__start_time__ = perf_counter()

# Initialize regular logging
initialize_logger()
enable_cli_logging()
load_dotenv()

# Enable CLI logging if in development mode
# if os.getenv("ENVIRONMENT", "production") == "development" or (
# len(argv) > 1 and argv[1] == "--dev"
# ):
# enable_cli_logging()
# logger.warning("Running in development mode")

# Make sure working directory is properly set to the root of the project
__proper_wd__ = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Ensuring working directory is properly set to {__proper_wd__}")
os.chdir(__proper_wd__)

# Constants
TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents(
    guilds=True,
    guild_messages=True,
    guild_reactions=True,
    messages=True,
    message_content=True,
    reactions=True,
    webhooks=True,
    moderation=True,
)

logger.info("Creating bot instance...")
bot = commands.Bot(command_prefix="-", intents=INTENTS)


@bot.event
@logger.catch
async def on_ready():
    """Initializes cogs on bot startup

    Begins logging
    Loads all cogs
    Sets status
    Finishes startup log
    """

    await enable_discord_logging(bot)

    # Startup status
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="Booting"),
        status=discord.Status.dnd,
    )

    logger.info("##############################")
    logger.info("# BOT STARTING FROM FULL SHUTDOWN #")
    logger.info("##############################")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing, name="Loading Cogs"
        ),
        status=discord.Status.idle,
    )

    for file in os.listdir("Cogs"):
        if not file.startswith("__") and file.endswith(".py"):
            try:
                await bot.load_extension(f"Cogs.{file[:-3]}")
                logger.success(f"Loaded cog: {file[:-3]}")
            except commands.errors.NoEntryPointError:
                logger.error(f"Cog {file[:-3]} has no setup function, cannot load.")
            except Exception as e:
                logger.error(f"Failed to load cog {file[:-3]}: {e}")

    # Show the bot as online
    # If the bot had a status prior to shutting down, restore it
    # if it didn't, set it to 'Raider Up!'
    contents = "Raider Up!"

    try:
        with open("status.txt", encoding="utf-8", mode="r") as sf:
            contents = sf.read()
    except FileNotFoundError:
        with open("status.txt", encoding="utf-8", mode="w") as sf:
            sf.write("Raider Up!")

    # try:
    # async with aiofiles.open("status.txt", mode="r") as sf:
    # contents = await sf.read()
    # except FileNotFoundError:
    # async with aiofiles.open("status.txt", mode="w") as sf:
    # await sf.write("Raider Up!")

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name=contents),
        status=discord.Status.online,
    )

    logger.success("Bot is online")

    logger.success("#########################")
    logger.success("  BOT STARTUP COMPLETED  ")
    logger.success("#########################")
    logger.success(f"Started in {round(perf_counter() - __start_time__, 2)} seconds")


@bot.event
@logger.catch
async def on_command_error(ctx, error):
    """Generic error handler

    If a command errors with a MissingRequiredArgument, MissingRole, or CommandNotFound error, triggers custom error message.
    If other error type, sends message with error statement
    """
    author, message = ctx.author, ctx.message.content

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument")
        await ctx.send_help()
        logger.warning(
            f"{author} attempted to run `{message}` but failed because they were missing a required argument",
        )

    elif isinstance(error, commands.MissingRole):
        await ctx.send("Missing role")
        logger.warning(
            f"{author} attempted to run `{message}` but failed because they were missing a required role",
        )

    elif isinstance(error, commands.CommandNotFound):
        logger.warning(
            f"{author} attempted to run `{message}` but failed because the command was not found",
        )

    else:
        await ctx.send(f"Unexpected error: {error}")
        logger.warning(
            f"{author} attempted to run `{message}` but failed because of an unexpected error: {error}",
        )


if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.run(TOKEN)
