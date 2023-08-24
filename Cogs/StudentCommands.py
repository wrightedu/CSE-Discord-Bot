import itertools
import random
import yaml
from os.path import exists
from pathlib import Path
from random import randint

from discord.ext import commands
from discord import app_commands

from utils.utils import *
from diceParser import parse
# from utils.Checkin import Checkin


async def setup(bot:commands.Bot):
    await bot.add_cog(StudentCommands(bot))


class StudentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Get a cute picture of some corgis!") 
    async def corgme(self, interaction:discord.Interaction, number:int =-1):
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
            await download_corgis(self.bot, interaction, 100)

        # Get images from directory
        images = ['dogs/corgis/' + path.name for path in Path('dogs').rglob('*.*')]

        # If 404, send cute error
        if number == 404:
            await interaction.response.send_message(f'Corgi #{number}:', file=discord.File('assets/Corgi404Error.png'))
            return

        # Generates a random number if no number is given
        elif number < 0 or number > (len(images) - 1):
            number = randint(0, len(images) - 1)

        image = images[number]

        # Send image
        await interaction.response.send_message(f'Corgi #{number}:', file=discord.File(image))

        # put in the log channel that the corgme command was run
        await log(self.bot, f'{interaction.user} ran /corgme in #{interaction.channel}')


    @app_commands.command(description='Displays the code needed to print "hello world" to the console')
    async def helloworld(self, interaction:discord.Interaction, language: str ='random'):
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

    @app_commands.command(description="Create a poll users can vote on")
    async def poll(self, interaction:discord.Interaction, question:str, option1: str, option2: str, option3: str = 'None', option4: str = 'None', 
    option5: str = 'None', option6: str = 'None', option7: str = 'None', option8: str = 'None', option9: str = 'None', option10: str = 'None'):
        """Create a poll that users can vote on
        Generates a dictionary from the passed in parameters of the command. Appends to the options list from 
        the inputted values determined from the optional parameters. Determine what the most appropriate 
        reactions for voting will be for the poll. Generate a two column format with reaction
        emojis on the left and options on the right. Embed this and display this in the discord chat.
        Log the creation of the poll.

        Args:
            question (str): A question that the poll taker is asking. 
            options (individual strs): String parameters for the desired options for the poll. 8 of them are optional

        Outputs:
            Message stating the question of the poll with answers bound to numeric emojis. Reacts to the message with those emojis
        """

        # slices the dictionary of local variables (the parameters) from the 3rd-10th options
        params = dict(itertools.islice(locals().items(), 5, 13))
        options = [option1, option2]    
        for param in params:
            choice = params[param] # sets the current choice to the value at the current key
            if choice != 'None':
                options.append(choice)

        # Define reactions
        if len(options) == 2 and options[0].casefold() == 'yes' and options[1].casefold() == 'no':
            reactions = ['✅', '❌']
        elif len(options) == 2 and options[0].casefold() == 'no' and options[1].casefold() == 'yes':
            reactions = ['❌', '✅']
        else:
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

        description = []
        for i, option in enumerate(options):
            description += '\n {} {}'.format(reactions[i], option)
        embed = discord.Embed(title=question, description=''.join(description))

        await interaction.response.send_message(embed=embed)
        react_message = await interaction.original_response() # store original message to add reactions to
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)

        # Logging
        await log(self.bot, f'{interaction.user} started a poll in #{interaction.channel}:')
        await log(self.bot, question, False)
        for option in options:
            await log(self.bot, f'{option}', False)

    @app_commands.command(description="Rolls dice based on input") 
    async def roll(self, interaction:discord.Interaction, roll:str):
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

        # make the roll into a list
        options=[roll]

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
