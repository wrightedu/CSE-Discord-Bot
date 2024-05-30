#!/usr/bin/env python
import os
from time import time
import logging
import logging.handlers
from dotenv import load_dotenv

import discord
from discord.ext import commands

# Configure logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf=8',
    maxBytes=32 * 1024 * 1024, # 32 MiB
    backupCount=5, # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also output to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Initialize bot
intents = discord.Intents(messages=True, guilds=True, members=True, voice_states=True, message_content=True)
bot = commands.Bot(command_prefix='-', intents=intents)
start_time = time()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


@bot.event
async def on_ready():
    """Initializes cogs on bot startup"""

    logger.info('Bot is starting up...')
    await bot.change_presence(activity=discord.Game('Booting'), status=discord.Status.dnd)
    logger.info('Changed status to Booting.')

    logger.info('Loading cogs...')
    for file in os.listdir('Cogs'):
        if not file.startswith('__') and file.endswith('.py'):
            try:
                await bot.load_extension(f'Cogs.{file[:-3]}')
                logger.info("Loaded cog: %s", {file[:-3]})
            except commands.errors.NoEntryPointError:
                logger.warning("No entry point found for cog: %s", {file[:-3]})


    # Show the bot as online
    # If the bot had a status prior to shutting down, restore it
    # if it didn't, set it to 'Raider Up!'

    try:
        async with aiofiles.open('status.txt', mode='r') as sf:
            contents = await sf.read()
    except FileNotFoundError:
        async with aiofiles.open('status.txt', mode='w') as sf:
            await sf.write('Raider Up!')
            contents = 'Raider Up!'
        
    await bot.change_presence(activity=discord.Game(contents), status=discord.Status.online)
    logger.info("Bot status set to %s", {contents})
    logger.info("Bot startup completed in %s seconds.", {round(time() - start_time, 1)})


@bot.event
async def on_command_error(ctx, error):
    """Generic error handler

    If a command errors with a MissingRequiredArgument, MissingRole, or CommandNotFound error, triggers custom error message.
    If other error type, sends message with error statement
    """
    author, message = ctx.author, ctx.message.content

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required argument')
        await ctx.send_help()
        logger.warning("%s attempted to run `%s` but failed: Missing required argument", {author}, {message})
    elif isinstance(error, commands.MissingRole):
        await ctx.send('Missing role')
        logger.warning("%s attempted to run `%s` but failed: Missing role", {author}, {message})
    elif isinstance(error, commands.CommandNotFound):
        logger.warning("%s attempted to run `%s` but failed: Command not found", {author}, {message})
    else:
        await ctx.send(f'Unexpected error: {error}')
        logger.error("%s attempted to run `%s` but failed: %s", {author}, {message}, {error})


if __name__ == '__main__':
    # Run bot from key given by command line argument
    bot.run(TOKEN, log_handler=None) # Suppress default logging
