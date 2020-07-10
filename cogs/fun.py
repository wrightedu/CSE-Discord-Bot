from datetime import datetime
from os.path import exists
from pathlib import Path
from random import randint

import discord
from bing_image_downloader import downloader
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ###### ================================== ######
    ######              Commands              ######
    ###### ================================== ######

    @commands.command()
    async def corgme(self, ctx):
        # Check if corgis dir exists
        if not exists('corgis'):
            await ctx.send('One moment, looking for corgis')
            downloader.download('corgi',
                                limit=100,
                                output_dir='corgis',
                                adult_filter_off=False,
                                force_replace=False)

        # Get images from directory
        images = []
        for path in Path('corgis').rglob('*.*'):
            images.append(path.name)

        # Pick a random image
        image = images[randint(0, len(images) - 1)]

        # Send image
        await ctx.send(content='Corgi!', file=image)


def setup(bot):
    bot.add_cog(Fun(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
