import random
import yaml
from os.path import exists
from pathlib import Path
from random import randint

from discord.ext import commands
from discord import app_commands

from utils.utils import *
from diceParser import parse


async def setup(bot:commands.Bot):
    await bot.add_cog(StudentCommands(bot))


class StudentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # going to be removed, not slash commanding it
    @commands.command()
    async def attendance(self, ctx):
        """Sends a list of all members in the same voice channel as the command author
        If the command author is in a voice channel with at least one other member,
        sends a message containing the name of the voice channel and @mentions of all the members in that channel, except the command author
        """

        # Gets users in the same voice chat as the requester and lists their @'s.
        try:
            channel = ctx.message.author.voice.channel
            members = channel.members
            members.remove(ctx.author)
            if members:
                attendees = "\n".join([member.mention for member in members])
                await ctx.message.channel.send(f"Attendees of {channel.name} required by {ctx.message.author.mention}:\n {attendees}")
            else:
                await ctx.message.channel.send("There are no users in your voice channel.")
        except AttributeError:
            await ctx.message.channel.send(f"You must be in a voice channel to use this command.")

    @commands.command(aliases=['corgmi']) #TODO: Remove?
    #@app_commands.command(description="Get a cute picture of some corgis!") 
    #TODO: make ^ into issue, explain optional parameter issue
    async def corgme(self, ctx, number=-1):
        """Sends a picture of a corgi
        Check to see if the corgis directory exists. If not, download 100 images and make a log of the event.
        Loop through all images in the directory containing pictures and place them in a list of images.
        If no number was input by user, select a random image from the list and send it in chat. If the user
        did input a number, use it as the index for the picture list and send the appropriate picture in chat.
        The number 404 is a special case.

        Args:
            number (int): ID number of the picture. Can be used to find specific corgi pictures from the existing list

        Outputs:
            image: picture being sent to chat
        """

        # Check if corgis dir exists
        if not exists('dogs/corgis'):
            await log(self.bot, 'Corgis directory not found, downloading 100 images')
            await download_corgis(self.bot, ctx, 100)

        # Get images from directory
        images = ['dogs/corgis/' + path.name for path in Path('dogs').rglob('*.*')]

        # If 404, send cute error
        if number == 404:
            await ctx.send(file=discord.File('assets/Corgi404Error.png'))
            return

        # Generates a random number if no number is given
        elif number < 0 or number > (len(images) - 1):
            number = randint(0, len(images) - 1)

        image = images[number]

        # Send image
        await ctx.send(f'Corgi #{number}:', file=discord.File(image))

        # put in the log channel that the corgme command was run
        await log(self.bot, f'{ctx.author} ran /corgme in #{ctx.channel}')

    # @commands.command()
    # async def helloworld(self, ctx, language='random'):
    @app_commands.command(description='Displays the code needed to print "hello world" to the console')
    async def helloworld(self, interaction:discord.Interaction, language: str ='random'):
        #TODO: make ^ into issue, explain optional parameter issue
        """Displays the code needed to print 'hello world' to the console in a variety of different programming languages
        Take in user input for a programming language. If input is ls, list all the languages that the command
        can give code for. If input is not listed in the keys for output or is 'random', pick a random language
        to display. If input is valid, display example code for the language of choice in chat and create a log
        of event.

        Args:
            language (str): Allows the user to determine what coding language will be displayed

        Outputs:
            Sample code for a 'Hello World' program in a chosen or random language
        """

        # Read in the langague data from the yaml file
        with open('helloworld.yml', 'r') as f:

            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            language_data = yaml.load(f, Loader=yaml.FullLoader)

        # clean input
        language = language.lower()

        # List languages
        if language == 'ls':
            languages = [i for i in language_data]
            languages.sort()
            languages = '\n'.join(languages)
            await interaction.response.send_message(f'```I know:\n{languages}```')
            return

        # If invalid input, make it random
        if language != 'random' and language not in language_data:
            language = 'random'

        # If random, pick random language
        if language == 'random':
            languages = [i for i in language_data]
            language = random.choice(languages)

        # Build the message
        message = f'{language}\n```{language_data[language]["tag"]}\n{language_data[language]["code"]}\n```'
        await interaction.response.send_message(message)
        await log(self.bot, f'{interaction.user} ran /helloworld with language {language} in #{interaction.channel}')

    @app_commands.command(description="Sends message containing Discord WebSocket protocol latency")
    async def ping(self, interaction:discord.Interaction):
        """Sends the Discord WebSocket protocol latency
        Sends a message containing the Discord WebSocket protocol latency. Log that the command was run.

        Outputs:
            Sends a message containing the Discord WebSocket protocol latency
        """

        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'{latency} ms')
        await log(self.bot, f'{interaction.user} pinged from #{interaction.channel}, response took {latency} ms')

    @app_commands.command(description="Create a poll users can vote on, put spaces between options, quotes around multiple word options")
    #@commands.command()
    #async def poll(self, ctx, question, *options: str):
    # async def poll(self, interaction:discord.Interaction, question:str, options: str):
    async def poll(self, interaction:discord.Interaction, question:str, option1: str, option2: str, option3: str = 'None', option4: str = 'None', 
    option5: str = 'None', option6: str = 'None', option7: str = 'None', option8: str = 'None', option9: str = 'None', option10: str = 'None'):
        """Create a poll that users can vote on
        Delete user message to call command. Prompt user to enter correct number of messages if command is called
        impoperly. Determine what the most approptiate reactions for voting will be for the poll. Create a list
        of descriptions for each option that poll takers can choose from. Generate a two column format with reaction
        images on the left and options on the right. Embed this and display this in the discord chat.
        Log the creation of the poll.

        Args:
            question (str): A question that the poll taker is asking. 
            options (tuple (str)): A set of options for users to choose. Put a space between each option
                May have multiple entries

        Outputs:
            Message stating the question of the poll with answers bound to numeric emojis. Reacts to the message with those emojis
        """

        # make a list of options, always have 2, the rest are optional, add if exist
        # TODO: Try if can use locals() and start at 3rd item and run thru like list
        options = [option1, option2]
        if (option3 != 'None'):
            options.append(option3)
        if (option4 != 'None'):
            options.append(option4)
        if (option5 != 'None'):
            options.append(option5)
        if (option6 != 'None'):
            options.append(option6)
        if (option7 != 'None'):
            options.append(option7)
        if (option8 != 'None'):
            options.append(option8)
        if (option9 != 'None'):
            options.append(option9)
        if (option10 != 'None'):
            options.append(option10)
        # Delete sender's messctxe
        # await interaction.channel.purge(limit=1)

        # Need between 2 and 10 options for a poll
        if not (1 < len(options) <= 10):
            await interaction.response.send_message('Enter between 2 and 10 answers')
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

        await interaction.response.send_message(embed=embed)
        react_message = await interaction.original_message() # store original message to add reactions to
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)

        # Logging
        await log(self.bot, f'{interaction.user} started a poll in #{interaction.channel}:')
        await log(self.bot, question, False)
        for option in options:
            await log(self.bot, f'{option}', False)

    @app_commands.command(description="Rolls dice based on input") 
    # @commands.command()
    # async def roll(self, ctx, *options):
    async def roll(self, interaction:discord.Interaction, roll:str, mod:str = 'None'):
        """Rolls dice based on input
        Check to see if the input is an appropriate size and quantity. Call imported dice parse module and store in
        'output'. 'output'[0] is the raw roll, and 'output'[1] is the roll with all modifiers included. If the length
        of the raw roll exceeds 100, the final tally is displayed to the chat. Otherwise, both the raw roll and final
        tally are displayed. An exception is called if the parse method cannot accept the input, and a log of the event
        is created. If the input is too large, the user is informed of this, and the user as well as failed call
        attempt are logged.

        Args:
            options(tuple(str)): Input to dice parser. String of various different forms

        Outputs:
            Result of dice rolled and pruned, or otherwise specified
        """

        # add the roll and if there's a mod to a list
        options=[roll]
        if (mod != 'None'):
            options.append(mod)

        # Credit goes to Alan Fleming for the module that powers this command
        # https://github.com/AlanCFleming/DiceParser
        dice = ' '.join(options)
        if 0 < len(dice) < 20 and dice.find('d') < 5:
            try:
                output = parse(dice)
                if len(output[0]) > 100:
                    await interaction.response.send_message(output[1]) # interaction.response.send_message
                else:
                    await interaction.response.send_message(f'{output[0]}\n{output[1]}')
                await log(self.bot, f'{interaction.user} successfully ran /roll in #{interaction.channel}')
            except Exception:
                await interaction.response.send_message('Invalid input')
                await log(self.bot, f'{interaction.user} unsuccessfully ran /roll in #{interaction.channel}, errored because input was invalid')
        else:
            await interaction.response.send_message('Too large of an input')
            await log(self.bot, f'{interaction.user} unsuccessfully ran /roll in #{interaction.channel}, errored because input was too large')

    # not implementing slash command for this command since it currently is not developed
    # @app_commands.command(description="TBD planned support command")
    # async def support(self, interaction:discord.Interaction):
        # """A planned support command
        # Informs user that the command is not yet available.

        # Outputs:
        #     error message explaining that the command is not yet available.
        # """
        # await interaction.response.send_message(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @them or email them at cse-support.wright.edu')
    
    @commands.command()
    async def support(self, ctx):
        """A planned support command
        Informs user that the command is not yet available.

        Outputs:
            error message explaining that the command is not yet available.
        """

        await ctx.send(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @them or email them at cse-support.wright.edu')
