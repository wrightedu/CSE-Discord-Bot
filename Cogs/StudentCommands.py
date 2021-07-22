import random
from os.path import exists
from pathlib import Path
from random import randint

import discord
from discord.ext import commands
from utils import *

from diceParser import parse


def setup(bot):
    bot.add_cog(StudentCommands(bot))


class StudentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['corgmi'])
    async def corgme(self, ctx, number=-1):
        """Sends a picture of a corgi
        Check to see if the corgis directory exists. If not, download 100 images and make a log of the event.
        Loop through all images in the directory containing pictures and place them in a list of images.
        If no number was input by user, select a random image from the list and send it in chat. If the user
        did input a number, use it as the index for the picture list and send the appropriate picture in chat.

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

        # Generates a random number if no number is given
        if number < 0:
            number = randint(0, len(images) - 1)
        image = images[number]

        # Send image
        await ctx.send(f'Corgi #{number}:', file=discord.File(image))
        await log(self.bot, f'{ctx.author} ran /corgme in #{ctx.channel}')

    @commands.command()
    async def helloworld(self, ctx, language='random'):
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
                   'cobol': '```cobol\n       identification division.\n       program-id. cobol.\n       procedure division.\n       main.\n           display \'Hello world!\' end-display.\n           stop run.```',
                   'papyrus': '```papyrus\nScriptname helloworld\n\nEvent OnPlayerLoadGame()\n\tDebug.Notification("Hello World!")\nEndEvent```'}

        # List languages
        if language == 'ls':
            languages = [i for i in outputs]
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
            languages = [i for i in outputs]
            language = random.choice(languages)

        await ctx.send(f'{language}\n{outputs[language]}')
        await log(self.bot, f'{ctx.author} ran /helloworld with language {language} in #{ctx.channel}')

    @commands.command()
    async def poll(self, ctx, question, *options: str):
        """Create a poll that users can vote on
        Delete user message to call command. Prompt user to enter correct number of messages if command is called
        impoperly. Determine what the most approptiate reactions for voting will be for the poll. Create a list
        of descriptions for each option that poll takers can choose from. Generate a two column format with reaction
        images on the left and options on the right. Embed this and display this in the discord chat.
        Log the creation of the poll.

        Args:
            question (str): A question that the poll taker is asking. Should be encapsulated by a set of quotation marks.
            options (tuple (str)): A set of options for users to choose. Each option should be encapsulated by a set of quotation marks.
                May have multiple entries

        Outputs:
            Message stating the question of the poll with answers bound to numeric emojis. Reacts to the message with those emojis
        """

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
        await log(self.bot, f'{ctx.author} started a poll in #{ctx.channel}:')
        await log(self.bot, question, False)
        for option in options:
            await log(self.bot, f'{option}', False)

    @commands.command()
    async def roll(self, ctx, *options):
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

        # Credit goes to Alan Fleming for the module that powers this command
        # https://github.com/AlanCFleming/DiceParser
        dice = ' '.join(options)
        if 0 < len(dice) < 20 and dice.find('d') < 5:
            try:
                output = parse(dice)
                if len(output[0]) > 100:
                    await ctx.send(output[1])
                else:
                    await ctx.send(f'{output[0]}\n{output[1]}')
                await log(self.bot, f'{ctx.author} successfully ran /roll in #{ctx.channel}')
            except Exception:
                await ctx.send('Invalid input')
                await log(self.bot, f'{ctx.author} unsuccessfully ran /roll in #{ctx.channel}, errored because input was invalid')
        else:
            await ctx.send('Too large of an input')
            await log(self.bot, f'{ctx.author} unsuccessfully ran /roll in #{ctx.channel}, errored because input was too large')

    @commands.command()
    async def support(self, ctx):
        """A planned support command
        Informs user that the command is not yet available.

        Outputs:
            error message explaining that the command is not yet available.
        """

        await ctx.send(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @them or email them at cse-support.wright.edu')

    @commands.command()
    async def ping(self, ctx):
        """Sends the Discord WebSocket protocol latency
        Sends a message containing the Discord WebSocket protocol latency. Log that the command was run.

        Outputs:
            Sends a message containing the Discord WebSocket protocol latency
        """

        latency = round(self.bot.latency * 1000)
        await ctx.send(f'{latency} ms')
        await log(self.bot, f'{ctx.author} pinged from #{ctx.channel}, response took {latency} ms')

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
