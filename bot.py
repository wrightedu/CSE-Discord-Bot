#!/usr/bin/env python
import json
import os
import random
import re
from datetime import datetime
from os.path import exists
from pathlib import Path
from random import randint
from time import sleep, time

import aiofiles
import discord
from bing_image_downloader import downloader
from discord.ext import commands
from dotenv import load_dotenv

from diceParser import parse


##### ======= #####
##### GLOBALS #####
##### ======= #####
client = discord.Client()
client = commands.Bot(command_prefix='-')
invites = {}
invites_json = None
reaction_roles = {}
reaction_message_ids = []
start_time = time()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAME = os.getenv('DISCORD_GUILD')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')


##### =========== #####
##### CORE EVENTS #####
##### =========== #####
@client.event
async def on_ready():
    global invites_json
    global reaction_roles

    await log('###################################')
    await log('# BOT STARTING FROM FULL SHUTDOWN #')
    await log('###################################')

    # # Load invites JSON
    # with open('invites.json', 'r') as f:
    #     invites_json = json.loads(f.read())
    # await log('Invites JSON loaded')

    # # Get invite links
    # for guild in client.guilds:
    #     invites[guild.id] = await guild.invites()
    # await log('Invites synced')

    # Initialize each guild
    for guild in client.guilds:
        await log(f'Initializing server: {guild}')
        # Load reaction roles JSONs
        reaction_roles_filename = f'reaction_roles_{guild.id}.json'
        # Load reaction roles from file
        if exists(reaction_roles_filename):
            with open(reaction_roles_filename, 'r') as f:
                reaction_roles[guild.id] = (guild, json.loads(f.read()))

        # Generate role menu
        try:
            await create_role_menu(guild)
        except Exception:
            await log(f'    failed, no reaction roles JSON')

    # Show the bot as online
    await client.change_presence(activity=discord.Game('Raider Up!'), status=None, afk=False)
    await log('Bot is online')

    # Print startup duration
    await log('#########################')
    await log('# BOT STARTUP COMPLETED #')
    await log('#########################\n')
    await log(f'Started in {round(time() - start_time, 1)} seconds')


@client.event
async def on_command_error(ctx, error):
    author, message = ctx.author, ctx.message.content

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required arguement')
        await ctx.send_help()
        await log(f'{author} attempted to run `{message}` but failed because they were missing a required argument')

    elif isinstance(error, commands.MissingRole):
        await ctx.send('Missing role')
        await log(f'{author} attempted to run `{message}` but failed because they were missing a required role')

    elif isinstance(error, commands.CommandNotFound):
        await log(f'{author} attempted to run `{message}` but failed because the command was not found')

    else:
        await ctx.send(f'Unexpected error: {error}')
        await log(f'{author} attempted to run `{message}` but failed because of an unexpected error: {error}')


##### ================== #####
##### MEMEBER MANAGEMENT #####
##### ================== #####
@client.event
async def on_member_join(member):
    invites_before_join = invites[member.guild.id]
    invites_after_join = await member.guild.invites()

    # Figure out which invite link was used
    for invite in invites_before_join:
        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
            invites[member.guild.id] = invites_after_join

            # Assign role (and notify if prospective student)
            for link in invites_json.keys():
                if invite.code in link:
                    await log(f'{invites_json[link]["purpose"]} {member.name} has joined ({link})')
                    role = discord.utils.get(member.guild.roles, id=invites_json[link]['roleID'])
                    await member.add_roles(role)
                    await log(f'Assigned role {role} to {member.name}')

                    # If prospective student, message in Prospective Student General
                    if invites_json[link]['purpose'] == 'Prospective student':
                        prospective_student_general_channel_id = 702895094881058896
                        prospective_student_general_channel = client.get_channel(prospective_student_general_channel_id)
                        channel = client.get_channel(702895094881058896)
                        await channel.send(f'Hello, {member.mention}')
            break


@client.event
async def on_raw_reaction_add(payload):
    global reaction_roles

    try:
        if payload.message_id in reaction_message_ids:
            # Get guild
            guild_id = payload.guild_id
            guild = discord.utils.find(lambda g: g.id == guild_id, client.guilds)

            # Get guild reaction roles
            guild_reaction_roles = reaction_roles[guild_id][1]

            # Find a role corresponding to the emoji name.
            classes = []
            for menu in guild_reaction_roles.keys():
                for class_name in guild_reaction_roles[menu].keys():
                    if class_name not in ['channel_name', 'clear_channel']:
                        classes.append(guild_reaction_roles[menu][class_name])
            role = None
            for _class in classes:
                emoji = f':{_class["emoji"]}:'
                if emoji in str(payload.emoji):
                    role = discord.utils.find(lambda r: r.name == _class['role'].replace(' ', ''), guild.roles)

            # If role found, assign it
            if role is not None:
                member = await guild.fetch_member(payload.user_id)
                if not member.bot:  # Error suppression
                    # Get class name from role
                    await member.add_roles(role)
                    await dm(member, f'Welcome to {role}!')
                    await log(f'Assigned role {role} to {member}')
    except Exception:
        await log('Error suppressed, likely due to bot reacting to a role menu')


@client.event
async def on_raw_reaction_remove(payload):
    if payload.message_id in reaction_message_ids:
        # Get guild
        guild_id = payload.guild_id
        guild = discord.utils.find(lambda g: g.id == guild_id, client.guilds)

        # Get guild reaction roles
        guild_reaction_roles = reaction_roles[guild_id][1]

        # Find a role corresponding to the emoji name.
        classes = []
        for menu in guild_reaction_roles.keys():
            for class_name in guild_reaction_roles[menu].keys():
                if class_name not in ['channel_name', 'clear_channel']:
                    classes.append(guild_reaction_roles[menu][class_name])
        role = None
        for _class in classes:
            emoji = f':{_class["emoji"]}:'
            if emoji in str(payload.emoji):
                role = discord.utils.find(lambda r: r.name == _class['role'].replace(' ', ''), guild.roles)

        # If role found, take it
        if role is not None:
            member = await guild.fetch_member(payload.user_id)
            await member.remove_roles(role)
            await dm(member, f'We\'ve taken you out of {role}')
            await log(f'Took role {role} from {member}')


##### ================ #####
##### STUDENT COMAMNDS #####
##### ================ #####
@client.command()
async def support(ctx):
    await ctx.send(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @ them or email them at cse-support.wright.edu')


@client.command()
async def corgme(ctx, number=-1):
    # Check if corgis dir exists
    if not exists('corgis'):
        await log('Corgis directory not found, downloading 100 images')
        downloadcorgis(100)

    # Get images from directory
    images = []
    for path in Path('corgis').rglob('*.*'):
        images.append('corgis/corgi/' + path.name)

    # Pick a random image
    if number != -1 and (0 < number < len(images)):
        image = images[number]
    else:
        image = images[randint(0, len(images) - 1)]

    # Send image
    await ctx.send(file=discord.File(image))
    await log(f'{ctx.author} ran /corgme in #{ctx.channel}')


@client.command()
async def poll(ctx, question, *options: str):
    # Delete sender's message
    await ctx.channel.purge(limit=1)

    # Need between 2 and 10 options for a poll
    if not (1 < len(options) <= 10):
        await ctx.send('Enter between 2 and 10 answers')
        return

    # Define reactions
    if len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
        reactions = ['✅', '❌']
    else:
        reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

    description = []
    for i, option in enumerate(options):
        description += '\n {} {}'.format(reactions[i], option)
    embed = discord.Embed(title=question, description=''.join(description))

    react_message = await ctx.send(embed=embed)
    for reaction in reactions[:len(options)]:
        await react_message.add_reaction(reaction)

    # Logging
    await log(f'{ctx.author} started a poll in #{ctx.channel}:')
    await log(question, False)
    for option in options:
        await log(f'{option}', False)


@client.command()
async def helloworld(ctx, language='random'):
    outputs = {'python': '```python\nprint("Hello World!")```',
               'c++': '```c++\n#include <iostream>\n\nint main() {\n    std::cout << "Hello world!" << std::endl;\n}```',
               'java': '```java\npublic class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello world!");\n    }\n}```',
               'c': '```c\n#include <stdio.h>\n\nint main() {\n    printf("Hello world!\\n");\n    return 0;\n}```',
               'bash': '```bash\necho "Hello world!"```',
               'javascript': '```javascript\nconsole.log("Hello world!");```',
               'brainf': '```\n++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.```',
               'rust': '```rust\nfn main() {\n    println!("Hello World!");\n}```',
               'matlab': '```matlab\ndisp(\'hello world\')```',
               'html': '```html\n<!DOCTYPE html>\n\n<html>\n  <head>\n    <title>Hello world!</title>\n    <meta charset="utf-8" />\n  </head>\n\n  <body>\n    <p>Wait a minute. This isn\'t a programming language!</p>\n  </body>\n</html>```',
               'csharp': '```csharp\nnamespace CSEBot {\n    class HelloWorld {\n        static void Main(string[] args) {\n            System.Console.WriteLine("Hello World!");\n        }\n    }\n}```',
               'vb': '```vb\nImports System\n\nModule Module1\n    Sub Main()\n        Console.WriteLine("Hello World!")\n        Console.WriteLine("Press Enter Key to Exit.")\n        Console.ReadLine()\n    End Sub\nEnd Module```',
               'r': '```r\nprint("Hello World!", quote = FALSE)```',
               'go': '```go\npackage main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello world!")\n}```',
               'swift': '```swift\nimport Swift\nprint("Hello world!")```',
               'haskell': '```haskell\nmodule Main where\nmain = putStrLn "Hello World"```',
               'befunge': '```befunge\n64+"!dlrow olleH">:#,_@```',
               'perl': '```perl\nprint "Hello world!"```',
               'php': '```php\n<?php\necho \'Hello World\';\n?>```',
               'lisp': '```lisp\n(DEFUN hello ()\n  (PRINT (LIST \'HELLO \'WORLD))\n)\n(hello)```',
               'basic': '```basic\n10 PRINT "Hello World"\n20 END```',
               'cobol': '```cobol\n       identification division.\n       program-id. cobol.\n       procedure division.\n       main.\n           display \'Hello world!\' end-display.\n           stop run.```'}

    # List languages
    if language == 'ls':
        languages = [i for i in outputs.keys()]
        languages.sort()
        languages = '\n'.join(languages)
        await ctx.send(f'I know:\n{languages}')
        return

    # If invalid input, make it random
    language = language.lower()
    if language != 'random' and language not in outputs.keys():
        language = 'random'

    # If random, pick random language
    if language == 'random':
        languages = [i for i in outputs.keys()]
        language = random.choice(languages)

    await ctx.send(f'{language}\n{outputs[language]}')
    await log(f'{ctx.author} ran /helloworld with language {language} in #{ctx.channel}')


@client.command()
async def roll(ctx, *options):
    # Credit goes to Alan Fleming for the module that powers this command
    # https://github.com/AlanCFleming/DiceParser
    dice = ' '.join(options)
    if 0 < len(dice) < 20 and dice.find('d') < 5:
        try:
            output = parse(dice)
            if len(output[0]) > 100:
                await ctx.send(output[1])
                await log(f'{ctx.author} successfully ran /roll in #{ctx.channel}')
            else:
                await ctx.send(f'{output[0]}\n{output[1]}')
                await log(f'{ctx.author} successfully ran /roll in #{ctx.channel}')
        except Exception:
            await ctx.send('Invalid input')
            await log(f'{ctx.author} unsuccessfully ran /roll in #{ctx.channel}, errored because input was invalid')
    else:
        await ctx.send('Too large of an input')
        await log(f'{ctx.author} unsuccessfully ran /roll in #{ctx.channel}, errored because input was too large')


##### ============== #####
##### ADMIN COMMANDS #####
##### ============== #####
@client.command()
@commands.has_permissions(administrator=True)
async def buildserver(ctx):
    global reaction_roles

    guild = ctx.guild
    reaction_roles_filename = f'reaction_roles_{guild.id}.json'

    # If reaction roles specified in attachment
    if len(ctx.message.attachments) > 0:
        try:
            os.remove(reaction_roles_filename)
        except FileNotFoundError:
            pass
        await ctx.message.attachments[0].save(reaction_roles_filename)
        with open(reaction_roles_filename, 'r') as f:
            reaction_roles[guild.id] = (guild, json.loads(f.read()))
        guild_reaction_roles = reaction_roles[ctx.guild.id]

    # If reaction roles not loaded for this guild, try to load from file
    if ctx.guild.id not in reaction_roles.keys():
        # Next try to load from file
        if exists(reaction_roles_filename):
            with open(reaction_roles_filename, 'r') as f:
                reaction_roles[guild.id] = (guild, json.loads(f.read()))
            guild_reaction_roles = reaction_roles[ctx.guild.id]

        # Finally give up on loading and terminate command
        else:
            await ctx.send('Reaction roles JSON not found, rerun command with JSON attached')
            await log('Reaction roles JSON not found, rerun command with JSON attached')
            return

    # If reaction roles JSON found (or attached)
    await log(f'BUILDING SERVER {ctx.guild} ({ctx.author})')
    await destroy_server(ctx, ctx.guild)
    await build_server(ctx, ctx.guild)
    await log('Recreating reaction role menus')
    await create_role_menu(ctx.guild)


@client.command()
@commands.has_permissions(administrator=True)
async def destroyserver(ctx):
    await log(f'DESTROYING SERVER ({ctx.author})')
    await destroy_server(ctx, ctx.guild)


@client.command()
@commands.has_permissions(administrator=True)
async def rolemenu(ctx):
    global reaction_roles

    guild = ctx.guild
    reaction_roles_filename = f'reaction_roles_{guild.id}.json'

    # If reaction roles specified in attachment
    if len(ctx.message.attachments) > 0:
        try:
            os.remove(reaction_roles_filename)
        except FileNotFoundError:
            pass
        await ctx.message.attachments[0].save(reaction_roles_filename)
        with open(reaction_roles_filename, 'r') as f:
            reaction_roles[guild.id] = (guild, json.loads(f.read()))

    await create_role_menu(ctx.guild)


@client.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=''):
    if amount == 'all':
        await ctx.send(f'Clearing all messages from this channel')
        await log(f'{ctx.author} cleared {amount} messages from #{ctx.channel}')
        amount = 999999999999999999999999999999999999999999
    elif amount == '':
        await ctx.send(f'No args passed. Use `/clear AMOUNT` to clear AMOUNT messages. Use `/clear all` to clear all messages from this channel')
        await log(f'{ctx.author} attempted to clear messages from #{ctx.channel}, but it failed because parameter "amount" was not passed')
        return
    else:
        await ctx.send(f'Clearing {amount} messages from this channel')
        await log(f'{ctx.author} cleared {amount} messages from #{ctx.channel}')
    sleep(1)
    await ctx.channel.purge(limit=int(float(amount)) + 2)


@client.command()
@commands.has_permissions(administrator=True)
async def downloadcorgis(ctx, amount):
    try:
        amount = int(amount)
        await ctx.send(f'Downloading {amount} images')
    except Exception:
        amount = 100
        await ctx.send(f'Invalid parameter, downloading {amount} images')
    downloader.download('corgi',
                        limit=amount,
                        output_dir='corgis',
                        adult_filter_off=False,
                        force_replace=False)
    await log(f'{ctx.author} ran /downloadcorgis {amount} in #{ctx.channel}')


@client.command()
@commands.has_permissions(administrator=True)
async def status(ctx, *, status):
    status = status.strip()
    if status.lower() == 'none':
        await client.change_presence(activity=None)
        await log(f'{ctx.author} disabled the custom status')
    elif len(status) <= 128:
        await client.change_presence(activity=discord.Game(status))
        await log(f'{ctx.author} changed the custom status to "Playing {status}"')


@client.command()
async def ping(ctx):
    latency = round(client.latency * 1000)
    await ctx.send(f'{latency} ms')
    await log(f'{ctx.author} pinged from #{ctx.channel}, response took {latency} ms')


@client.command()
@commands.has_permissions(administrator=True)
async def clearrole(ctx, *, role_id):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, id=int(role_id[3:-1]))

    cleared_members = []

    await log(f'{ctx.author} is clearing {role} from all members:')
    for member in role.members:
        await member.remove_roles(role)
        await log(member, False)
        cleared_members.append(member.nick)

    if len(cleared_members) > 10:
        await ctx.send(f'Cleared @{role} from {len(cleared_members)} members')
    elif len(cleared_members) == 0:
        await ctx.send(f'No members have the role @{role}')
    else:
        await ctx.send(f'Cleared @{role} from {", ".join(cleared_members)}')


##### ================= #####
##### UTILITY FUNCTIONS #####
##### ================= #####
async def log(string, timestamp=True):
    # Log to stdout
    timestamp_string = ''
    if timestamp:
        timestamp_string = f'[{str(datetime.now())[:-7]}]'
    print(timestamp_string + ' ' + string)

    # Log to channel
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == 'bot-logs':
                await channel.send(string)

    # Log to file
    try:
        async with aiofiles.open('log', mode='r') as f:
            previous_logs = await f.readlines()
    except FileNotFoundError:
        previous_logs = []

    async with aiofiles.open('log', mode='w') as f:
        for line in previous_logs:
            await f.write(line.strip() + '\n')
        await f.write(timestamp_string + ' ' + string + '\n')


async def create_role_menu(guild):
    global reaction_roles

    def get_emoji(emoji_name):
        emoji = discord.utils.get(client.emojis, name=emoji_name)
        if emoji is not None:
            return emoji
        return f':{emoji_name}:'

    # Get this guild's reaction roles
    guild_reaction_roles = reaction_roles[guild.id]

    # Generate list of menus to iterate through when sending messages
    menus = []
    clear_channel = False
    for key in guild_reaction_roles[1].keys():
        menus.append((key, guild_reaction_roles[1][key]))

    # Generate each menu independently
    for menu in menus:
        # Get channel object
        channel_name = menu[1]['channel_name']
        reaction_role_channel = None
        for channel in guild.channels:
            if channel.name.strip().lower() == channel_name.strip().lower():
                reaction_role_channel = channel

        # Clear channel if necessary
        if bool(menu[1]['clear_channel']):
            await reaction_role_channel.purge(limit=99999999999999)

        # Send menus
        message = f'__**{menu[0].strip()}**__\n'
        if not bool(menu[1]['clear_channel']):
            message = f'_ _\n__**{menu[0].strip()}**__\n'
        for option_name in menu[1].keys():
            if option_name not in ['channel_name', 'clear_channel']:
                emoji = str(get_emoji(menu[1][option_name]['emoji']))
                message += f'{emoji} `{option_name}`\n'
        reaction_message = await reaction_role_channel.send(message)

        # React to menu
        for option_name in menu[1].keys():
            if option_name not in ['channel_name', 'clear_channel']:
                emoji = get_emoji(menu[1][option_name]['emoji'])
                await reaction_message.add_reaction(emoji)

            # Put reaction message ids in global list
            reaction_message_ids.append(reaction_message.id)


def find_invite_by_code(invite_list, code):
    for invite in invite_list:
        if invite.code == code:
            return invite


async def destroy_server(ctx, guild):
    # Deletes all class channels/categories
    class_names = re.compile('\\w{2,3} \\d{4}')
    role_names = re.compile('\\w{2,3}\\d{4}')

    # List all categories that will be deleted and get confirmation before actually deleting
    deletion_list_message = 'The following categories will be deleted:\n'
    for category in guild.categories:
        if class_names.match(category.name):
            deletion_list_message += category.name + '\n'
    await ctx.send(deletion_list_message)

    # Wait for confirmation
    if await confirmation(ctx, 'confirm'):
        # Find all matching categories in the guild
        for category in guild.categories:
            if class_names.match(category.name):

                # Delete all channels in the category
                for channel in category.channels:
                    await channel.delete()

                # Delete the category itself
                await category.delete()

        # Delete class roles
        for role in guild.roles:
            if role_names.match(role.name):
                await role.delete()


async def build_server(ctx, guild):
    global reaction_roles

    # Builds new class channels/categories from reaction roles
    class_names = re.compile('\\w{2,3} \\d{4}')
    guild_reaction_roles = reaction_roles[guild.id][1]

    # # List all categories that will be created and get confirmation before actually creating
    creation_list_message = 'The following categories will be created:\n'
    for menu in guild_reaction_roles:
        for _class in guild_reaction_roles[menu]:
            if class_names.match(_class):
                class_number = guild_reaction_roles[menu][_class]['role']
                creation_list_message += class_number + '\n'
    await ctx.send(creation_list_message)

    # Wait for confirmation
    if await confirmation(ctx, 'confirm'):
        # Iterate through all menus in reaction roles
        for menu in guild_reaction_roles:
            # Iterate through all classes in each menu
            for _class in guild_reaction_roles[menu]:
                # Ignore menu properties
                if class_names.match(_class):

                    class_number = guild_reaction_roles[menu][_class]['role']

                    # Create class role
                    permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True, connect=True, speak=True, stream=True, use_voice_activation=True, change_nickname=True, mention_everyone=False)
                    print(f'Creating role: {class_number.replace(" ", "")}')
                    await guild.create_role(name=class_number.replace(' ', ''), permissions=permissions)

                    # Create category
                    category = await guild.create_category(class_number)
                    await category.set_permissions(guild.default_role, read_messages=False)
                    for role in guild.roles:
                        if role.name == class_number.replace(' ', ''):
                            await category.set_permissions(role, read_messages=True)
                            break

                    # Create channels
                    text_channel = await category.create_text_channel(class_number.replace(' ', ''))
                    await text_channel.edit(topic=_class)
                    await category.create_voice_channel('Student Voice')
                    await category.create_voice_channel('TA Voice', user_limit=2)


async def confirmation(ctx, confirm_string):
    # Ask for confirmation
    await ctx.send(f'Enter `{confirm_string}` to confirm action')

    # Wait for confirmation
    msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    if msg.content == confirm_string:
        await ctx.send(f'Action confirmed, executing')
        return True
    else:
        await ctx.send(f'Confirmation failed, terminating execution')
        return False


async def dm(member, content):
    channel = await member.create_dm()
    await channel.send(content)


if __name__ == '__main__':
    # Run bot from key given by command line argument
    client.run(TOKEN)
