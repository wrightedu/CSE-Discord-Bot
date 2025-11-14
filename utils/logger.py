"""
Logger setup using Loguru

This file contains all the configuration setup for the logger
this includes intercepting the standard discord.py logging to
use loguru instead for standardization.
The goal is to make one logger config and to not need to touch
it again unless it is a critical change.

- initialize_logger() - Call this once to set up the logger
- enable_cli_logging() - Call this to add CLI logging output
"""

# System Imports
import logging
from os import getenv
from sys import stdout
from itertools import chain

# Library Imports
import asyncio
import discord
from loguru import logger
from discord.ext.commands import Bot
from dotenv import load_dotenv

load_dotenv()
LOG_CHANNEL_ID = getenv("LOG_CHANNEL_ID")

discord_message_queue = asyncio.Queue()


def initialize_logger():
    """
    Initialize the logger configuration.
    Call before any logging is needed.
    """
    setup_intercept()
    logger.remove()  # Remove the default stderr config

    logger.section = "==========================="  # Custom attribute for sections

    # Logs info and success
    logger.add(
        "logs/info.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {name: <16} | {message}",
        level="INFO",
        enqueue=True,
        rotation="00:00",  # Rotate at midnight
        retention="3 days",
        filter=lambda record: record["level"].name in ("INFO", "SUCCESS"),
    )

    logger.add(
        "logs/errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {name: <16} | {message}",
        level="ERROR",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        rotation="00:00",  # Rotate at midnight
        retention="1 week",
    )

    # Combined log file
    logger.add(
        "logs/combined.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {name: <16} | {message}",
        enqueue=True,
        rotation="00:00",  # Rotate at midnight
        retention="1 week",
    )


async def enable_discord_logging(bot: Bot):
    """
    Enable logging to a Discord channel.
    Call if you want to send logs to a specific Discord channel.
    """

    # First attach the bot instance to the logger for access in the sink
    logger.info("Enabling Discord logging, attaching bot instance...")

    log_channel = bot.get_channel(int(LOG_CHANNEL_ID)) if LOG_CHANNEL_ID else None

    async def message_queue_processor():
        await bot.wait_until_ready()
        while not bot.is_closed():
            message = await discord_message_queue.get()

            try:
                if log_channel:
                    await log_channel.send(message)
                else:
                    print("Log channel not found, cannot send Discord logs.")
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.5)
                continue
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 5))
                    await asyncio.sleep(retry_after)
                    await log_channel.send(message)
                else:
                    print(f"Failed to send log message to Discord: {e}")

            discord_message_queue.task_done()

    logger.info("Creating message queue processor...")
    bot.loop.create_task(message_queue_processor())

    def sink_filter(record):
        level = record["level"].name
        message = record["message"]

        if "rate limited" in message:
            return False  # Ignore rate limited logs and debug

        if level in ("DEBUG"):
            return False

        if record["extra"].get("discord") is False:
            return False

        return True

    logger.info("Adding Discord log sink...")
    logger.add(
        discord_log_sink,
        format="{message}",
        enqueue=True,
        filter=sink_filter,  # Ignore rate limited logs and debug
    )
    logger.success("Discord logging enabled!")


async def discord_log_sink(message):
    """
    Custom sink function that will also send all these logs into a discord channel.
    """

    level = message.record["level"].name
    content = message.record["message"]
    if content == logger.section:
        return

    await discord_message_queue.put(f"` {level: <7} `  {content}")
    await logger.complete()


def enable_cli_logging():
    """
    Enable logging to the command line interface (stdout).
    Call if terminal logging is desired (maybe for debugging).
    """

    logger.add(
        stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        + "<level>{level: <7}</level> | "
        + "<magenta>{name: <16}</magenta> | "
        + "<level>{message}</level>",
        enqueue=True,
    )


def setup_intercept():
    """
    Set up interception of standard logging to redirect to loguru.
    Call if you want to capture standard logging (e.g., from discord.py).
    This will intercept logs from discord.py itself since they have
    their own logging setup.
    """
    modules = (
        "discord",
        "discord.gateway",
        "discord.http",
        "discord.state",
        "discord.client",
        "discord.ext.commands",
    )

    for name in chain(("",), modules):
        mod = logging.getLogger(name)
        mod.handlers = [InterceptHandler()]
        mod.propagate = False


class InterceptHandler(logging.Handler):
    """
    Custom logging handler to intercept standard logging and redirect to loguru.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
