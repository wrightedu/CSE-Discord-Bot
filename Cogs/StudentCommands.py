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
        """Initialize the bot"""
        self.bot = bot

    @commands.command(aliases=['corgmi'])
    async def corgme(self, ctx, number=-1):
        """Output a picture of gif(pronounced 'gif') of a corgi
        Args: 
            number: ID number of the picture. Can be used to find specific corgi pictures

        Returns:
            images: Picture of a corgi"""

        # Check if corgis dir exists
        if not exists('dogs/corgis'):
            await log(self.bot, 'Corgis directory not found, downloading 100 images')
            await download_corgis(self.bot, ctx, 100)

        # Get images from directory
        images = ['dogs/corgis/' + path.name for path in Path('dogs').rglob('*.*')]
        print(images[0])

        # Pick a random image
        if number != -1 and (0 < number < len(images)):
            image = images[number]
        else:
            image = images[randint(0, len(images) - 1)]

        # Send image
        await ctx.send(file=discord.File(image))
        await log(self.bot, f'{ctx.author} ran /corgme in #{ctx.channel}')

    @commands.command()
    async def helloworld(self, ctx, language='random'):
    """Displays the code needed to print 'hello world' to the console in a variety of different programming languages

        Args: 
            language: Allows the user to determine what coding language will be displayed

        Returns:
            outputs: Sample code for a 'Hello World' program in a chosen or random language
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
                   'cobol': '```cobol\n       identification division.\n       program-id. cobol.\n       procedure division.\n       main.\n           display \'Hello world!\' end-display.\n           stop run.```'}

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

        Args:
            Question: A question that the poll taker is asking. Should be encapsulated by a set of quotation marks. 
            Options: A set of options for users to choose. Each option should be encapsulated by a set of quotation marks.
        
        Returns:
            embeded: A formatted version of the question and options
            reactions: A set of reactions for users to click on in order to vote in poll. """

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
        
        """Rolls dice of any size
        Args: 
            *options: size of dice being rolled. Should be input as 'd{number}'.
        Returns:
            output: random number between 1 and the size of die being rolled. """

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
        Args: 

        Returns:
            error message"""

        await ctx.send(f'This is a feature currently being developed. For now, if you have a question for CSE Support, @them or email them at cse-support.wright.edu')

    @commands.command()
    async def ping(self, ctx):
        """Determine the ping a user is experiencing
        Args: 

        Returns:
            latency: The amount of time taken for a computer to send a response back to the server"""

        latency = round(self.bot.latency * 1000)
        await ctx.send(f'{latency} ms')
        await log(self.bot, f'{ctx.author} pinged from #{ctx.channel}, response took {latency} ms')
